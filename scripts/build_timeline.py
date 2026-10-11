"""Build the frame-exact timeline, caption lines, SRT and corrected transcript from the edited narration.

usage: python build_timeline.py --work W [--fps 30] [--hold 1.5] [--static]
Needs: W/clean/recNN.wav and W/transcripts/cut/recNN.json (run transcribe.py --stage cut after every re-cut).
Writes:
  W/remotion/src/data/timeline.json   slides [{n, startFrame, frames, dur, words}] (+ fps, totalFrames)
  W/remotion/src/data/captions.json   one-line caption cues with word timings (absolute seconds)
  W/remotion/src/data/project.json    copy of W/project.json (palette, sections, logos, titles)
  W/delivery/<name>.srt + <name>_transcript.md   (with --static: <name>_slides_version.srt for the plain-slides video)
ASR fixes come from W/corrections.json: [["inter-anator agreement", "inter-annotator agreement"], ["micro F1", "macro-F1"], ...].
They change captions/SRT/transcript text only, never the audio.
"""
import glob, json, os, re
import soundfile as sf
from common import args_with_work, wp, load_json, save_json, project, join_split_tokens, apply_corrections


def extra(ap):
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--hold", type=float, default=1.5, help="seconds held after the last word of the talk")
    ap.add_argument("--static", action="store_true", help="also write the SRT for the plain slides version (no end hold)")


a = args_with_work(__doc__, extra)
W = a.work
P = project(W)
corr = load_json(os.path.join(W, "corrections.json"), [])
name = P.get("output_name", "talk")
recs = sorted(os.path.basename(f)[:5] for f in glob.glob(os.path.join(W, "clean", "rec*.wav")))
if not recs:
    raise SystemExit("no clean narration: run cut.py and enhance.py first")


def slide_words(rec):
    t = load_json(os.path.join(W, "transcripts", "cut", rec + ".json"))
    if t is None:
        raise SystemExit(f"missing transcripts/cut/{rec}.json: run transcribe.py --stage cut")
    words, prev = [], ""
    for seg in t:
        txt = seg["text"].strip()
        if prev and prev.lower().endswith(txt.lower().strip(".") + "."):  # Whisper boundary echo
            continue
        prev = txt
        words += [{"w": w["w"].strip(), "s": w["s"], "e": w["e"]} for w in seg["words"]]
    return words


slides, cum = [], 0.0
for rec in recs:
    info = sf.info(os.path.join(W, "clean", rec + ".wav"))
    dur = info.frames / info.samplerate
    raw_words = slide_words(rec)
    slides.append({"n": int(rec[3:]), "dur": round(dur, 4), "startFrame": round(cum * a.fps),
                   "words": [{"w": w["w"], "s": round(w["s"], 3), "e": round(w["e"], 3)} for w in raw_words]})
    cum += dur
for k, s in enumerate(slides):
    nxt = slides[k + 1]["startFrame"] if k + 1 < len(slides) else round(cum * a.fps) + round(a.hold * a.fps)
    s["frames"] = nxt - s["startFrame"]
total = slides[-1]["startFrame"] + slides[-1]["frames"]
tl = {"fps": a.fps, "totalFrames": total, "slides": slides}
rdata = wp(W, "remotion", "src", "data")
save_json(tl, os.path.join(rdata, "timeline.json"))
save_json(P, os.path.join(rdata, "project.json"))
print(f"timeline: {len(slides)} slides, {total} frames = {total / a.fps:.2f} s")


# ---------------------------------------------------------------- corrected words per slide
def corrected(rec):
    w = join_split_tokens(slide_words(rec))
    w = apply_corrections(w, corr)
    for x in w:  # Whisper starts a word that follows a pause too early: clamp
        x["s"] = max(x["s"], x["e"] - max(0.35, 0.09 * len(x["w"])))
    return w


per = {rec: corrected(rec) for rec in recs}

# ---------------------------------------------------------------- captions (balanced single lines, <= ~50 chars)
L = lambda ws: len(" ".join(x["w"] for x in ws))
caps = []
for s, rec in zip(slides, recs):
    off = s["startFrame"] / a.fps
    words = per[rec]
    phrases, cur = [], []
    for k, w in enumerate(words):
        cur.append(w)
        nxt = words[k + 1] if k + 1 < len(words) else None
        if nxt is None or w["w"].endswith((".", "?", "!")) or nxt["s"] - w["e"] > 0.6:
            phrases.append(cur)
            cur = []
    for ph in phrases:
        n = max(1, -(-L(ph) // 48), -(-int((ph[-1]["e"] - ph[0]["s"]) * 10) // 45))
        out, rest = [], ph
        for j in range(n, 1, -1):
            target, best = L(rest) / j, None
            for c in range(1, len(rest)):
                left = L(rest[:c])
                score = abs(left - target) - (7 if rest[c - 1]["w"].endswith(",") else 0)
                if left <= 50 and (best is None or score < best[0]):
                    best = (score, c)
            if best is None:
                break
            out.append(rest[:best[1]])
            rest = rest[best[1]:]
        out.append(rest)
        for ws in out:
            if ws:
                caps.append({"slide": s["n"], "words": [{"w": x["w"], "s": round(off + x["s"], 3), "e": round(off + x["e"], 3)} for x in ws]})
for i, c in enumerate(caps):
    c["start"] = round(max(0, c["words"][0]["s"] - 0.08), 3)
    end = c["words"][-1]["e"] + 0.35
    if i + 1 < len(caps):
        end = min(end, caps[i + 1]["words"][0]["s"] - 0.12)
    c["end"] = round(max(end, c["words"][-1]["e"]), 3)
    c["text"] = re.sub(r"\s+([.,?!])", r"\1", " ".join(x["w"] for x in c["words"]))
save_json(caps, os.path.join(rdata, "captions.json"))
print(f"captions: {len(caps)} lines, longest {max(len(c['text']) for c in caps)} chars")


# ---------------------------------------------------------------- SRT + transcript
def srt_time(t):
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def write_srt(path, starts):
    cues = []
    for (rec, off) in starts:
        cur = []
        words = per[rec]
        for k, w in enumerate(words):
            cur.append(w)
            nxt = words[k + 1] if k + 1 < len(words) else None
            txt = " ".join(x["w"] for x in cur)
            if nxt is None or len(txt) > 70 or nxt["s"] - w["e"] > 0.8 or (w["w"].endswith((".", "?", "!")) and len(txt) > 25) or w["e"] - cur[0]["s"] > 5.5:
                cues.append([off + cur[0]["s"], off + cur[-1]["e"] + 0.25, txt])
                cur = []
    for i in range(len(cues) - 1):
        cues[i][1] = min(cues[i][1], cues[i + 1][0] - 0.05)
    with open(path, "w", encoding="utf8") as f:
        for i, (s0, s1, t) in enumerate(cues, 1):
            if len(t) > 42:
                j = t.rfind(" ", 0, len(t) // 2 + 10)
                t = t[:j] + "\n" + t[j + 1:] if j > 0 else t
            f.write(f"{i}\n{srt_time(s0)} --> {srt_time(s1)}\n{t}\n\n")
    return len(cues)


dl = wp(W, "delivery")
n1 = write_srt(os.path.join(dl, f"{name}.srt"), [(rec, s["startFrame"] / a.fps) for s, rec in zip(slides, recs)])
if a.static:
    acc, st = 0.0, []
    for s, rec in zip(slides, recs):
        st.append((rec, acc))
        acc += s["dur"]
    write_srt(os.path.join(dl, f"{name}_slides_version.srt"), st)
titles = {s["n"]: (s.get("text") or [""])[0] for s in load_json(os.path.join(W, "deck", "slides.json"), [])}
with open(os.path.join(dl, f"{name}_transcript.md"), "w", encoding="utf8") as f:
    f.write(f"# {P.get('title', name)}: narration transcript\n\nTimes are positions in the animated video. Only speech-recognition errors and number formatting were corrected.\n")
    for s, rec in zip(slides, recs):
        txt = re.sub(r"\s+([.,?!])", r"\1", " ".join(x["w"] for x in per[rec]))
        f.write(f"\n## Slide {s['n']}: {titles.get(s['n'], '')}  [{srt_time(s['startFrame'] / a.fps)[:8]}]\n\n{txt}\n")
print(f"SRT: {n1} cues; transcript written to delivery/")
