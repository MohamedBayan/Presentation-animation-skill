"""Apply the editorial cut plan to the raw recordings -> W/cut/recNN.wav (+ recNN_map.json, cut_log.md).

usage: python cut.py --work W [--only rec03 rec05]

W/edit_plan.json (created with defaults if missing):
{
 "defaults": {"lead_in": 0.25, "tail": 0.35, "speech_thr": -32, "gap_thr": -50,
              "gap_sentence": 0.42, "gap_comma": 0.28, "gap_word": 0.18, "snap": 0.10, "xfade": 0.012},
 "recordings": {
   "rec04": {"remove": [{"start": 21.2, "end": 24.9, "reason": "RETAKE: abandoned 'We benchmark five models.'; corrected take kept"}]}
 }
}
Per recording:
  1. explicit removes (ORIGINAL seconds). Put both edges inside silence; each edge snaps to the quietest 10 ms within +/- snap.
     An edge inside continuous speech is allowed only at a verified dip (probe.py energy + probe.py join), flag it in the reason.
  2. keep lead_in s before the first and tail s after the last speech
  3. pauses (90 ms median level < gap_thr) longer than their cap are shortened; the cap depends on the word before the pause
     (from the raw transcript): sentence end -> gap_sentence, comma/;/: -> gap_comma, otherwise gap_word.
     -50 dBFS keeps breaths and quiet consonants inside the kept speech.
  4. pieces join with xfade-second linear crossfades; every join's level is logged (should be < -50 dBFS unless flagged)
"""
import json, os, glob
import numpy as np, soundfile as sf
from scipy.signal import medfilt
from common import args_with_work, wp, load_json, save_json

DEFAULTS = {"lead_in": 0.25, "tail": 0.35, "speech_thr": -32, "gap_thr": -50, "gap_sentence": 0.42, "gap_comma": 0.28,
            "gap_word": 0.18, "snap": 0.10, "xfade": 0.012}


def extra(ap):
    ap.add_argument("--only", nargs="*")


a = args_with_work(__doc__, extra)
W = a.work
plan_path = os.path.join(W, "edit_plan.json")
plan = load_json(plan_path)
if plan is None:
    plan = {"defaults": DEFAULTS, "recordings": {}}
    save_json(plan, plan_path)
    print("created edit_plan.json with defaults (no explicit removes yet)")
G = {**DEFAULTS, **plan.get("defaults", {})}
OUT = wp(W, "cut")
log_path = os.path.join(OUT, "cut_log.md")
log = ["# Cut log (original-recording timestamps)\n"]


def frame_db(x, sr, hop_s=0.01):
    hop = int(hop_s * sr)
    n = len(x) // hop
    return 20 * np.log10(np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-9), hop


def snap(t, db, hop, sr, win):
    i, w = int(t * sr / hop), max(1, int(win * sr / hop))
    lo, hi = max(0, i - w), min(len(db) - 1, i + w)
    j = lo + int(np.argmin(db[lo:hi + 1]))
    return j * hop / sr, db[j]


def silences(db, hop, sr, thr):
    out, i, n = [], 0, len(db)
    while i < n:
        if db[i] < thr:
            j = i
            while j < n and db[j] < thr:
                j += 1
            out.append((i * hop / sr, j * hop / sr))
            i = j
        else:
            i += 1
    return out


def assemble(sig, idx_src, pieces, sr, xf):
    n = int(xf * sr)
    ys, ids = [], []
    for k, (i0, i1) in enumerate(pieces):
        p, idx = sig[i0:i1].copy(), idx_src[i0:i1]
        if k > 0 and n > 0 and len(ys[-1]) > n and len(p) > n:
            r = np.linspace(0, 1, n)
            ys[-1][-n:] = ys[-1][-n:] * (1 - r) + p[:n] * r
            p, idx = p[n:], idx[n:]
        ys.append(p)
        ids.append(idx)
    return np.concatenate(ys), np.concatenate(ids)


recs = sorted(os.path.basename(f)[:5] for f in glob.glob(os.path.join(W, "raw", "rec*.wav")))
summary = []
for rec in recs:
    if a.only and rec not in a.only:
        continue
    spec = plan.get("recordings", {}).get(rec, {})
    cfg = {**G, **{k: v for k, v in spec.items() if k != "remove"}}
    x, sr = sf.read(os.path.join(W, "raw", rec + ".wav"))
    db, hop = frame_db(x, sr)
    log.append(f"\n## {rec}, original {len(x) / sr:.2f} s")
    removes = []
    for r in spec.get("remove", []):
        s0, d0 = snap(r["start"], db, hop, sr, cfg["snap"])
        s1, d1 = snap(r["end"], db, hop, sr, cfg["snap"])
        if s1 <= s0:
            raise SystemExit(f"{rec}: bad remove {r}")
        removes.append((s0, s1))
        log.append(f"- REMOVE {s0:7.2f}-{s1:7.2f} ({s1 - s0:5.2f} s; edges at {d0:.0f}/{d1:.0f} dB): {r.get('reason', '')}")
    removes.sort()
    keep, cur = [], 0.0
    for s0, s1 in removes:
        if s0 > cur:
            keep.append([cur, s0])
        cur = max(cur, s1)
    if cur < len(x) / sr:
        keep.append([cur, len(x) / sr])
    sm = medfilt(db, 9)
    speech = np.where(sm > cfg["speech_thr"])[0]
    if len(speech) == 0:
        print(f"{rec}: no speech detected, skipped")
        continue
    first, last = speech[0] * hop / sr, (speech[-1] + 1) * hop / sr
    lo, hi = max(0.0, first - cfg["lead_in"]), min(len(x) / sr, last + cfg["tail"])
    keep = [[max(s0, lo), min(s1, hi)] for s0, s1 in keep if min(s1, hi) > max(s0, lo)]
    y, oid = assemble(x, np.arange(len(x)), [(int(s0 * sr), int(s1 * sr)) for s0, s1 in keep], sr, cfg["xfade"])
    # context-dependent pause caps
    raw_words = []
    rawt = load_json(os.path.join(W, "transcripts", "raw", rec + ".json"), [])
    for sg in rawt:
        raw_words += sg.get("words", [])
    if not raw_words:
        print(f"{rec}: no raw transcript; every pause is treated as mid-sentence ({cfg['gap_word']} s). Run transcribe.py --stage raw first.")

    def target_for(orig_t):
        prev = [w for w in raw_words if w["e"] <= orig_t + 0.25]
        lw = prev[-1]["w"].strip() if prev else ""
        if lw.endswith((".", "?", "!")):
            return cfg["gap_sentence"], "sentence"
        if lw.endswith((",", ";", ":")):
            return cfg["gap_comma"], "comma"
        return cfg["gap_word"], "word"

    ydb, _ = frame_db(y, sr)
    pieces, cur, cnt = [], 0, {"sentence": 0, "comma": 0, "word": 0}
    for s0, s1 in silences(medfilt(ydb, 9), hop, sr, cfg["gap_thr"]):
        if s0 <= 0.05 or s1 >= len(y) / sr - 0.05:
            continue
        o0 = oid[min(len(oid) - 1, int(s0 * sr))] / sr
        tgt, kind = target_for(o0)
        if s1 - s0 > tgt + 0.04:
            c0, _ = snap(s0 + tgt / 2, ydb, hop, sr, 0.03)
            c1, _ = snap(s1 - tgt / 2, ydb, hop, sr, 0.03)
            if c1 > c0:
                pieces.append((cur, int(c0 * sr)))
                cur = int(c1 * sr)
                cnt[kind] += 1
                log.append(f"- pause after orig {o0:7.2f} s ({kind}): {s1 - s0:4.2f} s -> {tgt:.2f} s")
    pieces.append((cur, len(y)))
    y, oid = assemble(y, oid, pieces, sr, cfg["xfade"])
    jumps = np.where(np.diff(oid) != 1)[0]
    worst = max([db[min(len(db) - 1, int(t / hop))] for j in jumps for t in (oid[j], oid[j + 1])], default=-200)
    log.append(f"- joins: {len(jumps)}; loudest 10 ms frame at a join = {worst:.0f} dBFS")
    nf = int(0.02 * sr)
    y[:nf] *= np.linspace(0, 1, nf)
    y[-nf:] *= np.linspace(1, 0, nf)
    sf.write(os.path.join(OUT, rec + ".wav"), y.astype(np.float32), sr, subtype="PCM_24")
    m, rs = [], 0
    for j in list(jumps) + [len(oid) - 1]:
        m.append({"orig_start": round(oid[rs] / sr, 3), "orig_end": round((oid[j] + 1) / sr, 3), "new_start": round(rs / sr, 3)})
        rs = j + 1
    save_json({"rec": rec, "orig_dur": len(x) / sr, "new_dur": len(y) / sr, "keep": m}, os.path.join(OUT, rec + "_map.json"))
    log.append(f"- **{len(x) / sr:.2f} s -> {len(y) / sr:.2f} s**")
    flag = "" if worst < -50 else "  <- a join is above -50 dBFS: intended (flagged in plan)?"
    print(f"{rec}: {len(x) / sr:6.2f} -> {len(y) / sr:6.2f} s | {len(removes)} removes | pauses {cnt} | join max {worst:.0f} dBFS{flag}", flush=True)
    summary.append((rec, len(x) / sr, len(y) / sr))
# keep log entries of recordings not re-cut this time
old = open(log_path, encoding="utf8").read() if (a.only and os.path.exists(log_path)) else None
open(log_path, "w", encoding="utf8").write("\n".join(log) if not old else old + "\n" + "\n".join(log[1:]))
if summary:
    print(f"total {sum(s[1] for s in summary) / 60:.1f} min -> {sum(s[2] for s in summary) / 60:.1f} min")
