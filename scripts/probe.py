"""Small probes for deciding cut points.

  python probe.py --work W energy rec05 39.5 42.6 [--ms 20]
      level profile (dB RMS per bin) of the RAW recording, to find the quietest point between words
  python probe.py --work W join rec14 11.40-15.38 18.30-19.50
      concatenates the given ranges of the RAW recording (0.35 s silence between) and transcribes the result,
      so you can verify a candidate cut reads correctly BEFORE adding it to edit_plan.json
"""
import os, sys
import numpy as np, soundfile as sf
from common import args_with_work


def extra(ap):
    ap.add_argument("cmd", choices=["energy", "join"])
    ap.add_argument("rec")
    ap.add_argument("rest", nargs="+")
    ap.add_argument("--ms", type=float, default=50)


a = args_with_work(__doc__, extra)
x, sr = sf.read(os.path.join(a.work, "raw", a.rec + ".wav"))
if a.cmd == "energy":
    t0, t1 = float(a.rest[0]), float(a.rest[1])
    hop = int(a.ms / 1000 * sr)
    seg = x[int(t0 * sr):int(t1 * sr)]
    vals = [f"{t0 + i / sr:.2f}:{20 * np.log10(np.sqrt(np.mean(seg[i:i + hop] ** 2)) + 1e-9):4.0f}" for i in range(0, len(seg) - hop, hop)]
    for i in range(0, len(vals), 10):
        print("  " + "  ".join(vals[i:i + 10]))
else:
    from faster_whisper import WhisperModel
    m = WhisperModel("large-v3", device="cuda", compute_type="float16")
    z = np.zeros(int(0.35 * sr))
    parts = [z]
    for r in a.rest:
        s0, s1 = map(float, r.split("-"))
        parts += [x[int(s0 * sr):int(s1 * sr)], z]
    segs, _ = m.transcribe(np.concatenate(parts).astype(np.float32), language="en", beam_size=5, temperature=0.0, word_timestamps=True,
                           condition_on_previous_text=False)
    print(" ".join(w.word.strip() for s in segs for w in s.words))
