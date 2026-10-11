"""Plain slides version: each rendered slide image shown for exactly its narration clip, mastered to -16 LUFS.
Fast fallback / second deliverable; needs W/deck/slideNN.png and W/clean/recNN.wav.

usage: python slides_video.py --work W
"""
import glob, os
import soundfile as sf
from common import args_with_work, wp, project, ff, loudness

a = args_with_work(__doc__)
W = a.work
P = project(W)
FPS = 30
recs = sorted(os.path.basename(f)[:5] for f in glob.glob(os.path.join(W, "clean", "rec*.wav")))
tmp = wp(W, "out", "slides_version")
clips, t = [], 0.0
for rec in recs:
    n = int(rec[3:])
    info = sf.info(os.path.join(W, "clean", rec + ".wav"))
    clips.append((os.path.join(W, "deck", f"slide{n:02d}.png"), os.path.join(W, "clean", rec + ".wav"), info.frames / info.samplerate, t))
    t += info.frames / info.samplerate
starts = [round(c[3] * FPS) / FPS for c in clips] + [round(t * FPS) / FPS]
with open(os.path.join(tmp, "slides.txt"), "w", encoding="utf8") as f:
    for i, c in enumerate(clips):
        f.write(f"file '{c[0]}'\nduration {starts[i + 1] - starts[i]:.6f}\n")
    f.write(f"file '{clips[-1][0]}'\n")
with open(os.path.join(tmp, "audio.txt"), "w", encoding="utf8") as f:
    for c in clips:
        f.write(f"file '{c[1]}'\n")
nar = os.path.join(tmp, "narration.wav")
ff(["-y", "-f", "concat", "-safe", "0", "-i", os.path.join(tmp, "audio.txt"), "-ac", "2", "-ar", "48000", "-c:a", "pcm_f32le", nar], check=True)
I0, _, _ = loudness(nar)
out = os.path.join(wp(W, "delivery"), P.get("output_name", "talk") + "_slides_version.mp4")
ff(["-y", "-f", "concat", "-safe", "0", "-i", os.path.join(tmp, "slides.txt"), "-i", nar, "-fps_mode", "cfr", "-r", str(FPS),
    "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-profile:v", "high",
    "-af", f"volume={-16 - I0:.2f}dB,aresample=192000,alimiter=limit=0.84:attack=5:release=80:level=false,aresample=48000",
    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", "-t", f"{t:.3f}", out], check=True)
I, _, TP = loudness(out)
print(f"{out}: {t:.1f} s, {I:.1f} LUFS, TP {TP:.1f} dBTP")
