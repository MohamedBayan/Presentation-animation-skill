"""Conservative narration enhancement -> W/clean/recNN.wav (48 kHz, 24-bit, mono, about -16.5 LUFS, true peak -2 dBTP).

usage: python enhance.py --work W [--presence 2.0] [--mud -2.0]

Chain (validated on phone voice memos; the speaker approved it after rejecting heavier processing):
  SoX-quality resample to 48 kHz -> 80 Hz high-pass -> mud cut at 300 Hz -> presence boost at 2.6 kHz
  -> gentle 2:1 levelling above -22 dBFS -> static gain to -16 LUFS -> 4x-oversampled peak limiter at -2 dBFS
Deliberately NOT used (see references/audio.md): synthetic bandwidth extension / "AI super-resolution" (sounded unclear
and metallic), de-essers, noise gates, spectral noise reduction on already-clean phone audio.
"""
import glob, os, re
import numpy as np, soundfile as sf
from common import args_with_work, wp, ff, loudness, save_json


def extra(ap):
    ap.add_argument("--presence", type=float, default=2.0, help="dB at 2.6 kHz")
    ap.add_argument("--mud", type=float, default=-2.0, help="dB at 300 Hz")
    ap.add_argument("--target", type=float, default=-16.0)


a = args_with_work(__doc__, extra)
W = a.work
OUT = wp(W, "clean")
PRE = (f"aresample=48000:resampler=soxr:precision=28,highpass=f=80:poles=2,equalizer=f=300:t=q:w=1.1:g={a.mud},"
       f"equalizer=f=2600:t=q:w=1.0:g={a.presence},acompressor=threshold=-22dB:ratio=2:attack=12:release=180:knee=6:makeup=1")
stats = {}
for f in sorted(glob.glob(os.path.join(W, "cut", "rec*.wav"))):
    rec = os.path.basename(f)[:5]
    tmp = os.path.join(OUT, rec + "_tmp.wav")
    ff(["-y", "-i", f, "-af", PRE, "-c:a", "pcm_f32le", tmp], check=True)
    I0, _, TP0 = loudness(tmp)
    g = a.target - I0
    x, _ = sf.read(tmp)
    touched = float(np.mean(np.abs(x * 10 ** (g / 20)) > 10 ** (-2 / 20)) * 100)
    out = os.path.join(OUT, rec + ".wav")
    ff(["-y", "-i", tmp, "-af", f"volume={g:.2f}dB,aresample=192000,alimiter=limit=0.7943:attack=5:release=80:level=false,aresample=48000:resampler=soxr",
        "-ar", "48000", "-c:a", "pcm_s24le", out], check=True)
    os.remove(tmp)
    I, LRA, TP = loudness(out)
    stats[rec] = {"I": I, "TP": TP, "LRA": LRA, "limited_pct": round(touched, 3)}
    print(f"{rec}: {I:.1f} LUFS, TP {TP:.1f} dBTP, LRA {LRA:.1f}; limiter touches {touched:.2f}% of samples", flush=True)
save_json(stats, os.path.join(OUT, "loudness_stats.json"))
