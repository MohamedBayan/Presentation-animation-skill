"""Set up / refresh the Remotion project for a talk.

usage: python make_assets.py --work W [--update-template] [--install]
  - copies assets/remotion-template -> W/remotion (first run; --update-template refreshes the engine files but never
    touches W/remotion/src/scenes/ or src/data/)
  - paper textures in the project palette (light page + dark chapter page)
  - synthesized SFX palette (no third-party samples): whoosh, whoosh_soft, swish, thud, stamp, pop, pop_lo, tap, tick,
    counter, marker, pencil, scribble, paper, riser, chime
  - src/fontsData.ts: the bundled OFL fonts embedded as base64 (a render tab can never stall on a font request)
  - copies W/clean/recNN.wav -> public/audio/recNN.wav, W/deck/slideNN.png -> public/slides/, logos from project.json
  - --install runs npm install and downloads Remotion's headless Chrome
"""
import base64, glob, json, os, shutil, subprocess
import numpy as np, soundfile as sf
from PIL import Image, ImageFilter
from scipy.signal import butter, sosfilt, sosfiltfilt
from common import args_with_work, wp, project, SKILL_DIR


def extra(ap):
    ap.add_argument("--update-template", action="store_true")
    ap.add_argument("--install", action="store_true")


a = args_with_work(__doc__, extra)
W = a.work
P = project(W)
R = os.path.join(W, "remotion")
TPL = os.path.join(SKILL_DIR, "assets", "remotion-template")
def copy_template(engine_only):
    """engine files are always (re)copied; src/scenes and src/data only when missing, so generated data
    (build_timeline.py may run first) and your scenes are never overwritten"""
    for root, dirs, files in os.walk(TPL):
        dirs[:] = [d for d in dirs if d != "node_modules"]
        rel = os.path.relpath(root, TPL)
        user_owned = rel.replace("\\", "/").startswith(("src/scenes", "src/data"))
        for f in files:
            dst = os.path.join(R, rel, f)
            if user_owned and (engine_only or os.path.exists(dst)):
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(root, f), dst)


if not os.path.exists(os.path.join(R, "package.json")):
    copy_template(engine_only=False)
    print("copied Remotion template ->", R)
elif a.update_template:
    copy_template(engine_only=True)
    print("refreshed engine files (scenes and data untouched)")
pub = os.path.join(R, "public")
for d in ("img", "sfx", "audio", "slides", "img/logos"):
    os.makedirs(os.path.join(pub, d), exist_ok=True)
rng = np.random.RandomState(7)
pal = {"paper": "#F6F4EE", "ink": "#181050", **P.get("palette", {})}
hexrgb = lambda h: tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))


# ---------------------------------------------------------------- paper textures
def paper(base, amp_lo, amp_fine, path, fibers=True):
    Wd, Ht = 1920, 1080
    lo = Image.fromarray((rng.rand(Ht // 24, Wd // 24) * 255).astype(np.uint8)).resize((Wd, Ht), Image.BICUBIC).filter(ImageFilter.GaussianBlur(30))
    img = np.asarray(base, float)[None, None, :] + ((np.asarray(lo, float) / 255 - 0.5) * amp_lo)[..., None] + ((rng.rand(Ht, Wd) - 0.5) * amp_fine)[..., None]
    if fibers:
        fb = np.zeros((Ht, Wd))
        for _ in range(1400):
            x, y, Lf, ang = rng.randint(0, Wd), rng.randint(0, Ht), rng.randint(6, 26), rng.rand() * np.pi
            for k in range(Lf):
                xx, yy = int(x + k * np.cos(ang)), int(y + k * np.sin(ang))
                if 0 <= xx < Wd and 0 <= yy < Ht:
                    fb[yy, xx] += 1
        fb = np.asarray(Image.fromarray((np.clip(fb, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)), float) / 255
        img = img - fb[..., None] * 5
    yy, xx = np.mgrid[0:Ht, 0:Wd]
    r = np.sqrt(((xx - Wd / 2) / (Wd / 2)) ** 2 + ((yy - Ht / 2) / (Ht / 2)) ** 2)
    img = img * (1 - 0.06 * np.clip(r - 0.55, 0, 1) ** 1.5)[..., None]
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(path, optimize=True)


if not os.path.exists(os.path.join(pub, "img", "paper.png")) or a.update_template:
    paper(hexrgb(pal["paper"]), 10, 6, os.path.join(pub, "img", "paper.png"))
    paper(hexrgb(pal["ink"]), 10, 5, os.path.join(pub, "img", "paper_dark.png"), fibers=False)

# ---------------------------------------------------------------- SFX
SR = 48000
norm = lambda x, pk=0.89: x / (np.max(np.abs(x)) + 1e-9) * pk
env = lambda L, at, rl: np.minimum(1, np.arange(L) / SR / at) * np.exp(-np.arange(L) / SR / rl)
bp = lambda x, lo, hi: sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)


def sweep_noise(dur, f0, f1, q=1.6):
    L = int(dur * SR)
    x, y, seg = rng.randn(L), np.zeros(L), 256
    for i in range(0, L, seg):
        f = f0 * (f1 / f0) ** (i / L)
        y[i:i + seg] = bp(x[max(0, i - 2048):i + seg], max(40, f / q), min(SR / 2 - 100, f * q))[-len(y[i:i + seg]):]
    return y


def whoosh(dur=0.55, f0=300, f1=3500):
    y = sweep_noise(dur, f0, f1)
    t = np.arange(len(y)) / SR
    y = y * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2.2
    pan = np.clip(t / dur, 0, 1)
    return norm(np.stack([y * (1 - 0.6 * pan), y * (0.4 + 0.6 * pan)], 1))


def thud(f0=120, f1=50, dur=0.35):
    L = int(dur * SR)
    t = np.arange(L) / SR
    f = f0 * np.exp(np.log(f1 / f0) * t / dur)
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.09) + bp(rng.randn(L), 200, 2500) * np.exp(-t / 0.008) * 0.5)


def pop(f0=880, f1=440, dur=0.13):
    L = int(dur * SR)
    t = np.arange(L) / SR
    return norm(np.sin(2 * np.pi * np.cumsum(f0 * np.exp(np.log(f1 / f0) * t / dur)) / SR) * env(L, 0.002, 0.035))


def tick(f=3200):
    L = int(0.035 * SR)
    t = np.arange(L) / SR
    return norm(np.sin(2 * np.pi * f * t) * np.exp(-t / 0.005) + 0.3 * bp(rng.randn(L), 2000, 8000) * np.exp(-t / 0.002))


def counter(dur=0.9, n=18):
    L = int(dur * SR)
    o, k = np.zeros(L), tick(2600)
    for i in range(n):
        q = i / n
        j = min(L - len(k), int(dur * (1 - (1 - q) ** 1.8) * SR))
        o[j:j + len(k)] += k * (0.55 + 0.45 * (1 - q))
    return norm(o)


def textured(dur, lo, hi, rate, shape=0.8):
    L = int(dur * SR)
    t = np.arange(L) / SR
    x = bp(rng.randn(L), lo, hi)
    return norm(x * (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * rate * t))) * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** shape)


def stamp():
    s = thud(150, 60, 0.32)
    t = np.arange(len(s)) / SR
    return norm(s + norm(bp(rng.randn(len(s)), 900, 5000) * np.exp(-t / 0.02)) * 0.35)


def riser(dur=1.6):
    y = sweep_noise(dur, 200, 6000, q=1.3)
    t = np.arange(len(y)) / SR
    return norm((norm(y) * 0.8 + np.sin(2 * np.pi * np.cumsum(220 + 660 * (t / dur) ** 2) / SR) * 0.25) * (t / dur) ** 2.4)


def chime():
    t = np.arange(int(2.4 * SR)) / SR
    return norm(sum(am * np.sin(2 * np.pi * f * t) * np.exp(-t / d) for f, am, d in [(523.25, 1, 1.1), (659.25, .7, .9), (783.99, .6, .8), (1046.5, .3, .6)]) * np.minimum(1, t / 0.01))


def swish(dur=0.32):
    y = sweep_noise(dur, 700, 6500, q=1.4)
    return norm(y * np.sin(np.pi * np.clip(np.arange(len(y)) / SR / dur, 0, 1)) ** 1.6)


bank = {"whoosh": whoosh(), "whoosh_soft": whoosh(0.7, 200, 2200), "swish": swish(), "thud": thud(), "stamp": stamp(), "pop": pop(),
        "pop_lo": pop(560, 300, 0.15), "tap": norm(bp(rng.randn(int(0.09 * SR)), 400, 3000) * env(int(0.09 * SR), 0.001, 0.012)),
        "tick": tick(), "counter": counter(), "marker": textured(0.45, 1800, 7000, 23), "pencil": textured(0.6, 2500, 9000, 9, 0.6),
        "scribble": textured(0.5, 3000, 9500, 6.5, 0.5), "paper": textured(0.35, 1200, 6000, 40, 1.5), "riser": riser(), "chime": chime()}
for k, v in bank.items():
    v = v if v.ndim == 2 else np.stack([v, v], 1)
    sf.write(os.path.join(pub, "sfx", k + ".wav"), v.astype(np.float32), SR, subtype="PCM_16")

# ---------------------------------------------------------------- fonts as base64
fonts = {"INTER": "Inter-VF.ttf", "CAVEAT": "Caveat-VF.ttf", "CAIRO": "Cairo-VF.ttf"}
with open(os.path.join(R, "src", "fontsData.ts"), "w") as f:
    f.write("// generated by make_assets.py: fonts embedded as base64\n")
    for k, fn in fonts.items():
        f.write(f"export const {k} = '{base64.b64encode(open(os.path.join(pub, 'fonts', fn), 'rb').read()).decode()}';\n")

# ---------------------------------------------------------------- media
for f in glob.glob(os.path.join(W, "clean", "rec*.wav")):
    shutil.copy2(f, os.path.join(pub, "audio", os.path.basename(f)))
for f in glob.glob(os.path.join(W, "deck", "slide*.png")):
    shutil.copy2(f, os.path.join(pub, "slides", os.path.basename(f)))
# which slides have a rendered image: scenes/index.ts uses it to pick SlideScene vs PointsScene
have = sorted(int(os.path.basename(f)[5:7]) for f in glob.glob(os.path.join(pub, "slides", "slide[0-9][0-9].png")))
with open(os.path.join(R, "src", "data", "slide_images.json"), "w") as f:
    json.dump(have, f)
for group in P.get("logos", {}).values():
    for lg in (group if isinstance(group, list) else [group] if group else []):
        src = lg if os.path.isabs(lg) else os.path.join(W, lg)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(pub, "img", "logos", os.path.basename(src)))
        else:
            print("!! logo not found:", lg)
print(f"assets ready: {len(bank)} SFX, paper textures, fonts, {len(glob.glob(os.path.join(pub, 'audio', 'rec*.wav')))} narration clips, "
      f"{len(glob.glob(os.path.join(pub, 'slides', '*.png')))} slide images")
if a.install:
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    subprocess.run([npm, "install", "--no-audit", "--no-fund"], cwd=R, check=True)
    subprocess.run([shutil.which("npx") or shutil.which("npx.cmd"), "remotion", "browser", "ensure"], cwd=R)
