"""Island audit: split each recording at its pauses and transcribe EVERY piece on its own.

usage: python audit.py --work W --stage raw|cut [--only rec05]
Writes W/audit/<stage>_recNN.txt and prints suspects.

Why: whole-file Whisper silently merges retakes ("we collected 12000 que- ... we collected 12,000 questions" comes out once).
Transcribing each island alone exposes false starts, repeated words and abandoned sentences.
Suspects printed:
  REPEAT   island starts with the same 2+ words as the previous island (classic restart)
  ECHO     last word of an island == first word of the next ("understood. / Understood the wording")
  FRAGMENT very short island (< 4 words) followed by a pause, often an abandoned start
Read the full audit file anyway: restarts in *different words* are not caught automatically.
"""
import glob, os
import numpy as np, soundfile as sf
from scipy.signal import medfilt
from common import args_with_work, wp, norm


def extra(ap):
    ap.add_argument("--stage", choices=["raw", "cut"], required=True)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--thr", type=float, default=-40.0, help="island threshold on 90 ms median level (dBFS)")
    ap.add_argument("--min-gap", type=float, default=0.25)


a = args_with_work(__doc__, extra)
W = a.work
from faster_whisper import WhisperModel

try:
    model = WhisperModel("large-v3", device="cuda", compute_type="float16")
except Exception:
    model = WhisperModel("large-v3", device="cpu", compute_type="int8")
out = wp(W, "audit")
for f in sorted(glob.glob(os.path.join(W, a.stage, "rec*.wav"))):
    rec = os.path.basename(f)[:5]
    if a.only and rec not in a.only:
        continue
    x, sr = sf.read(f)
    if x.ndim > 1:
        x = x.mean(1)
    hop = int(0.01 * sr)
    n = len(x) // hop
    db = 20 * np.log10(np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-9)
    sp = medfilt(db, 9) > a.thr
    isl, i = [], 0
    while i < n:
        if sp[i]:
            j = i
            while j < n and sp[j]:
                j += 1
            isl.append([i * hop / sr, j * hop / sr])
            i = j
        else:
            i += 1
    merged = []
    for s0, s1 in isl:
        if merged and s0 - merged[-1][1] < a.min_gap:
            merged[-1][1] = s1
        else:
            merged.append([s0, s1])
    lines, texts = [], []
    for s0, s1 in merged:
        if s1 - s0 < 0.15:
            continue
        seg = np.concatenate([np.zeros(int(0.3 * sr)), x[int(max(0, s0 - 0.05) * sr):int(min(len(x) / sr, s1 + 0.1) * sr)], np.zeros(int(0.3 * sr))]).astype(np.float32)
        if sr != 16000:
            from scipy.signal import resample_poly
            seg = resample_poly(seg, 16000, sr).astype(np.float32)
        segs, _ = model.transcribe(seg, language="en", beam_size=5, temperature=0.0, condition_on_previous_text=False)
        t = " ".join(s.text.strip() for s in segs)
        texts.append((s0, s1, t))
        lines.append(f"  {s0:6.2f}-{s1:6.2f}  {t}")
    open(os.path.join(out, f"{a.stage}_{rec}.txt"), "w", encoding="utf8").write(f"=== {rec} ({a.stage})\n" + "\n".join(lines) + "\n")
    sus = []
    for k in range(1, len(texts)):
        p, c = [norm(w) for w in texts[k - 1][2].split()], [norm(w) for w in texts[k][2].split()]
        p, c = [w for w in p if w], [w for w in c if w]
        if len(p) >= 2 and len(c) >= 2 and p[:2] == c[:2]:
            sus.append(f"REPEAT   {texts[k-1][0]:.2f}-{texts[k][1]:.2f}: '{texts[k-1][2]}' / '{texts[k][2]}'")
        if p and c and p[-1] == c[0] and len(p[-1]) > 2:
            sus.append(f"ECHO     {texts[k-1][1]:.2f}/{texts[k][0]:.2f}: '...{texts[k-1][2][-30:]}' / '{texts[k][2][:30]}...'")
        if 0 < len(p) < 4 and not texts[k - 1][2].rstrip().endswith((".", "?", "!")):
            sus.append(f"FRAGMENT {texts[k-1][0]:.2f}-{texts[k-1][1]:.2f}: '{texts[k-1][2]}'")
    print(f"{rec}: {len(texts)} islands" + ("" if not sus else "\n    " + "\n    ".join(sus)), flush=True)
