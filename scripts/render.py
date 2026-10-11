"""One command from Remotion project to delivered, verified MP4s.

usage: python render.py --work W [--stages chunks,sfx,caps,master,mux,verify] [--chunks 8] [--concurrency 4] [--fresh]
Stages (default: all, in this order):
  chunks  picture of the Pipeline composition in frame-exact chunks, each retried up to 4x -> remotion/out/chunks/
          (existing chunks are reused; --fresh deletes them first: ALWAYS pass it after changing scenes, cues or timing)
  sfx     SFX-only audio stem (Pipeline with {"audio":"sfxOnly"}) -> W/out/sfx_stem.wav
  caps    transparent caption layer as PNGs -> W/out/caps/cap_%05d.png (chunked, retried)
  master  master_mix.py: narration + SFX stem -> -16 LUFS mix (also refreshes the Studio's mastered track)
  mux     mux.py twice: <name>_final.mp4 (captions) and <name>_final_no_captions.mp4
  verify  verify.py on the captioned file (with the Whisper sync check) and the clean file (without)
Why chunks + retries: a long single render occasionally dies when Remotion opens a late browser tab; a chunk retries cheaply.
"""
import glob, os, re, shutil, subprocess, sys, time
from common import args_with_work, wp, load_json

HERE = os.path.dirname(os.path.abspath(__file__))
ALL = ["chunks", "sfx", "caps", "master", "mux", "verify"]


def extra(ap):
    ap.add_argument("--stages", default=",".join(ALL))
    ap.add_argument("--chunks", type=int, default=8)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--fresh", action="store_true")


a = args_with_work(__doc__, extra)
W = a.work
R = os.path.join(W, "remotion")
NPX = shutil.which("npx") or shutil.which("npx.cmd")
tl = load_json(os.path.join(R, "src", "data", "timeline.json"))
TOTAL = tl["totalFrames"]
stages = [s.strip() for s in a.stages.split(",") if s.strip()]


def remotion(args, log):
    with open(log, "w", encoding="utf8") as f:
        return subprocess.run([NPX, "remotion", "render", "src/index.ts"] + args + ["--timeout=90000", "--log=error"],
                              cwd=R, stdout=f, stderr=subprocess.STDOUT).returncode


def first_error(log):
    txt = re.sub(r"\x1b\[[0-9;]*m", "", open(log, encoding="utf8", errors="replace").read())
    m = re.search(r".*error.*", txt, re.I)
    return m.group(0)[:200] if m else txt.strip()[-200:]


def ranges(k):
    sz = -(-TOTAL // k)
    return [(c, c * sz, min(TOTAL, (c + 1) * sz) - 1) for c in range(k) if c * sz < TOTAL]


def py(script, *args):
    subprocess.run([sys.executable, os.path.join(HERE, script), "--work", W, *args], check=True)


t_start = time.time()
if "chunks" in stages:
    cdir = os.path.join(R, "out", "chunks")
    if a.fresh and os.path.isdir(cdir):
        shutil.rmtree(cdir)
    os.makedirs(cdir, exist_ok=True)
    for c, A, B in ranges(a.chunks):
        f = os.path.join(cdir, f"c{c:02d}.mp4")
        if os.path.exists(f) and os.path.getsize(f) > 0:
            print(f"chunk {c} exists")
            continue
        for tr in range(1, 5):
            log = os.path.join(cdir, f"c{c:02d}.log")
            remotion(["Pipeline", f, "--codec=h264", "--crf=16", "--muted", f"--concurrency={a.concurrency}", f"--frames={A}-{B}"], log)
            if os.path.exists(f) and os.path.getsize(f) > 0:
                print(f"chunk {c} ({A}-{B}) ok on try {tr}")
                break
            print(f"chunk {c} try {tr} failed: {first_error(log)}")
            if os.path.exists(f):
                os.remove(f)
        else:
            sys.exit(f"chunk {c} failed 4 times, see {log}")
    with open(os.path.join(cdir, "list.txt"), "w") as f:
        f.writelines(f"file {os.path.basename(x)}\n" for x in sorted(glob.glob(os.path.join(cdir, "c*.mp4"))))
    old = os.path.join(W, "out", "video_noaudio.mp4")
    if os.path.exists(old):
        os.remove(old)   # mux.py re-joins from list.txt

if "sfx" in stages:
    out = os.path.join(wp(W, "out"), "sfx_stem.wav")
    for tr in range(1, 4):
        if remotion(["Pipeline", out, "--codec=wav", "--props=./sfx_props.json"], os.path.join(wp(W, "out"), "sfx_stem.log")) == 0:
            break
        print(f"sfx stem try {tr} failed")
    print("sfx stem ->", out)

if "caps" in stages:
    cap = wp(W, "out", "caps")
    if a.fresh:
        for f in glob.glob(os.path.join(cap, "cap_*.png")):
            os.remove(f)
    tmp = os.path.join(R, "out", "caps_tmp")
    for c, A, B in ranges(max(1, a.chunks // 2)):
        need = [i for i in range(A, B + 1) if not os.path.exists(os.path.join(cap, f"cap_{i:05d}.png"))]
        if not need:
            print(f"caps chunk {c} exists")
            continue
        for tr in range(1, 5):
            shutil.rmtree(tmp, ignore_errors=True)
            remotion(["CaptionsOnly", tmp, "--sequence", "--image-format=png", f"--frames={A}-{B}", f"--concurrency={a.concurrency}"],
                     os.path.join(R, "out", f"caps_c{c}.log"))
            got = glob.glob(os.path.join(tmp, "*.png"))
            if len(got) == B - A + 1:
                for g in got:   # Remotion names sequence frames by absolute frame number
                    os.replace(g, os.path.join(cap, f"cap_{int(re.findall(r'[0-9]+', os.path.basename(g))[-1]):05d}.png"))
                print(f"caps chunk {c} ({A}-{B}) ok on try {tr}")
                break
            print(f"caps chunk {c} try {tr} failed ({len(got)}/{B - A + 1})")
        else:
            sys.exit(f"caption chunk {c} failed 4 times")

if "master" in stages:
    py("master_mix.py")
if "mux" in stages:
    py("mux.py", "--captions")
    py("mux.py")
if "verify" in stages:
    name = load_json(os.path.join(W, "project.json"), {}).get("output_name", "talk")
    py("verify.py", "--video", os.path.join(W, "delivery", f"{name}_final.mp4"))
    py("verify.py", "--video", os.path.join(W, "delivery", f"{name}_final_no_captions.mp4"), "--no-sync")
print(f"RENDER_DONE in {(time.time() - t_start) / 60:.1f} min")
