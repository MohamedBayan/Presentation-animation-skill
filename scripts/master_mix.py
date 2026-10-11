"""Mix narration + SFX outside Remotion and master to -16 LUFS.

usage: python master_mix.py --work W [--sfx-peak -17.5] [--target -16]
Needs W/out/sfx_stem.wav, rendered with the Pipeline composition in SFX-only mode:
  npx remotion render src/index.ts Pipeline ../out/sfx_stem.wav --codec=wav --props=./sfx_props.json
Why not let Remotion mix: its mixer attenuated the mono narration by ~7.7 dB relative to the effects. Here the narration
is placed exactly at each slide's start frame at full level, the SFX stem is scaled so its PEAK sits at --sfx-peak
(narration peaks are about -2 dBTP, so effects stay ~15 dB under the voice), then static gain to --target LUFS and a
4x-oversampled peak limiter. Writes W/out/mix_master.wav and copies it to remotion/public/audio/final_mix_master.wav
(the track the Studio "Talk-final" composition plays: it must be regenerated after ANY timing change or the Studio
preview drifts out of sync).
"""
import os, shutil
import numpy as np, soundfile as sf
from common import args_with_work, wp, load_json, ff, loudness


def extra(ap):
    ap.add_argument("--sfx-peak", type=float, default=-17.5)
    ap.add_argument("--target", type=float, default=-16.0)


a = args_with_work(__doc__, extra)
W = a.work
OUT = wp(W, "out")
tl = load_json(os.path.join(W, "remotion", "src", "data", "timeline.json"))
SR = 48000
n = int(round(tl["totalFrames"] / tl["fps"] * SR))
nar = np.zeros(n)
for s in tl["slides"]:
    y, sr = sf.read(os.path.join(W, "clean", f"rec{s['n']:02d}.wav"))
    assert sr == SR, "clean narration must be 48 kHz (run enhance.py)"
    i = int(round(s["startFrame"] / tl["fps"] * SR))
    j = min(n, i + len(y))
    nar[i:j] += y[: j - i]
nar = np.stack([nar, nar], 1)
stem = os.path.join(OUT, "sfx_stem.wav")
if os.path.exists(stem):
    sfx, sr = sf.read(stem)
    sfx = np.stack([sfx, sfx], 1) if sfx.ndim == 1 else sfx
    sfx = sfx[:n] if len(sfx) >= n else np.vstack([sfx, np.zeros((n - len(sfx), 2))])
    pk = 20 * np.log10(np.max(np.abs(sfx)) + 1e-12)
    sfx = sfx * 10 ** ((a.sfx_peak - pk) / 20)
    print(f"sfx stem peak {pk:.1f} -> {a.sfx_peak} dBFS")
else:
    print("!! no out/sfx_stem.wav: mixing narration only")
    sfx = np.zeros_like(nar)
pre = os.path.join(OUT, "mix_premaster.wav")
sf.write(pre, (nar + sfx).astype(np.float32), SR, subtype="FLOAT")
I0, _, _ = loudness(pre)
g = a.target - I0
mst = os.path.join(OUT, "mix_master.wav")
ff(["-y", "-i", pre, "-af", f"volume={g:.2f}dB,aresample=192000,alimiter=limit=0.84:attack=3:release=60:level=false,aresample=48000",
    "-ar", "48000", "-c:a", "pcm_s24le", mst], check=True)
I, LRA, TP = loudness(mst)
print(f"master: {I:.1f} LUFS, LRA {LRA:.1f}, true peak {TP:.1f} dBTP, {n / SR:.2f} s (timeline {tl['totalFrames'] / tl['fps']:.2f} s)")
shutil.copy2(mst, wp(W, "remotion", "public", "audio", "final_mix_master.wav"))
