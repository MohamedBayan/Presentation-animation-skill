"""Split ONE long recording into per-slide clips (when the user recorded the whole talk in one take).

usage: python split.py --work W --source rec01 --plan W/split_plan.json
split_plan.json: [{"slide": 1, "start": 0.0, "end": 41.3}, {"slide": 2, "start": 41.3, "end": 88.0}, ...]
Pick boundaries inside pauses at slide transitions (use the raw transcript + probe.py energy). Each boundary is snapped to
the quietest 10 ms within +/- 0.3 s. Writes W/raw/recNN.wav per slide and rewrites W/mapping.json.
"""
import json, os
import numpy as np, soundfile as sf
from common import args_with_work, save_json, rec_id


def extra(ap):
    ap.add_argument("--source", required=True)
    ap.add_argument("--plan", required=True)


a = args_with_work(__doc__, extra)
x, sr = sf.read(os.path.join(a.work, "raw", a.source + ".wav"))
hop = int(0.01 * sr)
n = len(x) // hop
db = 20 * np.log10(np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-9)


def snap(t):
    i, w = int(t * sr / hop), int(0.3 * sr / hop)
    lo, hi = max(0, i - w), min(n - 1, i + w)
    return (lo + int(np.argmin(db[lo:hi + 1]))) * hop / sr


plan = json.load(open(a.plan, encoding="utf8"))
src_wav = os.path.join(a.work, "raw", a.source + ".wav")
os.replace(src_wav, os.path.join(a.work, "raw", "_full_" + a.source + ".wav"))
mapping = []
for p in plan:
    s0 = 0.0 if p["start"] <= 0 else snap(p["start"])
    s1 = len(x) / sr if p["end"] >= len(x) / sr else snap(p["end"])
    sf.write(os.path.join(a.work, "raw", rec_id(p["slide"]) + ".wav"), x[int(s0 * sr):int(s1 * sr)], sr, subtype="PCM_16")
    mapping.append({"slide": p["slide"], "file": f"raw/_full_{a.source}.wav", "start": round(s0, 3), "end": round(s1, 3), "duration": round(s1 - s0, 3)})
    print(f"slide {p['slide']:2d}: {s0:7.2f}-{s1:7.2f}")
save_json(mapping, os.path.join(a.work, "mapping.json"))
