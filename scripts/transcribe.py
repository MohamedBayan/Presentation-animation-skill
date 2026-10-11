"""Word-timestamped transcription with faster-whisper (large-v3 on CUDA, int8 on CPU).

usage: python transcribe.py --work W --stage raw|cut [--only rec03 rec07] [--model large-v3] [--language en]
  raw -> transcribes W/raw/recNN.wav into W/transcripts/raw/
  cut -> transcribes W/cut/recNN.wav into W/transcripts/cut/  (needed after every re-cut: animations and captions use these timings)
The initial prompt is built from the deck text so domain terms (model names, metrics) are spelled right.
"""
import glob, os, re, time
from common import args_with_work, wp, save_json, load_json, project


def extra(ap):
    ap.add_argument("--stage", choices=["raw", "cut"], required=True)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--language")


a = args_with_work(__doc__, extra)
W = a.work
from faster_whisper import WhisperModel

lang = a.language or project(W).get("language", "en")
slides = load_json(os.path.join(W, "deck", "slides.json"), [])
# domain prompt: distinctive capitalised / technical tokens from the deck, most frequent first
toks = {}
for s in slides:
    for line in s.get("text", []) + s.get("notes", []):
        for t in re.findall(r"[A-Za-z][A-Za-z0-9\-\.]*[A-Z0-9][A-Za-z0-9\-\.]*|[A-Z][a-z]+[A-Z][A-Za-z]*", line):
            if len(t) > 2:
                toks[t] = toks.get(t, 0) + 1
prompt = ", ".join(sorted(toks, key=lambda k: -toks[k])[:60]) + "." if toks else None
try:
    model = WhisperModel(a.model, device="cuda", compute_type="float16")
except Exception as e:
    print("CUDA unavailable, using CPU int8 (slower):", str(e)[:80])
    model = WhisperModel(a.model, device="cpu", compute_type="int8")
src = os.path.join(W, a.stage)
out = wp(W, "transcripts", a.stage)
for f in sorted(glob.glob(os.path.join(src, "rec*.wav"))):
    rec = os.path.basename(f)[:5]
    if a.only and rec not in a.only:
        continue
    t0 = time.time()
    segs, _ = model.transcribe(f, language=lang, beam_size=5, word_timestamps=True, initial_prompt=prompt,
                               vad_filter=False, condition_on_previous_text=False, temperature=0.0)
    res = [{"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip(),
            "words": [{"w": w.word, "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 3)} for w in (s.words or [])]} for s in segs]
    save_json(res, os.path.join(out, rec + ".json"))
    with open(os.path.join(out, rec + ".txt"), "w", encoding="utf8") as fh:
        for s in res:
            fh.write(f"[{s['start']:7.2f} - {s['end']:7.2f}] {s['text']}\n")
    print(f"{rec}: {len(res)} segments, {time.time() - t0:.0f}s", flush=True)
