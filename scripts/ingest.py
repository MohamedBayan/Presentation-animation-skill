"""Collect the user's files into <work>, map recordings to slides, decode audio, read and render the deck.

usage: python ingest.py --work W --recordings <dir|zip|file ...> [--deck talk.pptx|talk.pdf] [--first-slide N]

- Originals are never modified: recordings are copied/unzipped into W/input/, the deck is copied to W/deck/source.*
- Recording order: by embedded creation_time when every file has one, otherwise natural filename order
  (an unnumbered "Name.m4a" counts as #1 before "Name 2.m4a"). Both orders are printed; check them.
- One recording per slide is the common case. If there is ONE long recording for many slides, ingest maps it to slide 1
  and prints a hint: write W/split_plan.json and run split.py (see references/intake.md).
- Writes W/mapping.json, W/raw/recNN.wav (16 kHz mono), W/deck/slides.json, W/deck/slideNN.png, and a project.json skeleton.
"""
import os, re, json, shutil, subprocess, sys, zipfile, glob
from xml.etree import ElementTree as ET
from common import args_with_work, wp, save_json, load_json, ff, ffprobe, natural_key, rec_id, SKILL_DIR

AUDIO_EXT = (".m4a", ".mp3", ".wav", ".aac", ".ogg", ".opus", ".flac", ".caf", ".mp4", ".mov", ".m4v", ".webm", ".mkv")


def extra(ap):
    ap.add_argument("--recordings", nargs="+", required=True)
    ap.add_argument("--deck")
    ap.add_argument("--first-slide", type=int, default=1, help="slide number of the first recording (default 1)")


a = args_with_work(__doc__, extra)
W = a.work
inp = wp(W, "input", "recordings")

# ---------------------------------------------------------------- collect recordings
files = []
for src in a.recordings:
    if os.path.isdir(src):
        for f in os.listdir(src):
            if f.lower().endswith(AUDIO_EXT):
                shutil.copy2(os.path.join(src, f), os.path.join(inp, f))
    elif src.lower().endswith(".zip"):
        with zipfile.ZipFile(src) as z:
            for n in z.namelist():
                if n.lower().endswith(AUDIO_EXT) and not n.startswith("__MACOSX"):
                    target = os.path.join(inp, os.path.basename(n))
                    with z.open(n) as s, open(target, "wb") as d:
                        shutil.copyfileobj(s, d)
    elif src.lower().endswith(AUDIO_EXT):
        shutil.copy2(src, os.path.join(inp, os.path.basename(src)))
files = sorted(os.listdir(inp))
if not files:
    sys.exit("no recordings found")


def probe(f):
    out = subprocess.run([ffprobe(), "-v", "error", "-show_entries", "format=duration:format_tags=creation_time:stream=codec_type,sample_rate,channels",
                          "-of", "json", f], capture_output=True, text=True).stdout
    j = json.loads(out or "{}")
    fmt = j.get("format", {})
    aud = [s for s in j.get("streams", []) if s.get("codec_type") == "audio"]
    return {"duration": float(fmt.get("duration", 0)), "creation_time": fmt.get("tags", {}).get("creation_time"),
            "sample_rate": aud[0].get("sample_rate") if aud else None, "channels": aud[0].get("channels") if aud else None}


info = {f: probe(os.path.join(inp, f)) for f in files}


def name_key(f):
    stem = os.path.splitext(f)[0]
    m = re.search(r"(\d+)\s*$", stem)
    return (re.sub(r"[\s_-]*\d+\s*$", "", stem).lower(), int(m.group(1)) if m else 1, natural_key(f))


by_name = sorted(files, key=name_key)
by_time = sorted(files, key=lambda f: info[f]["creation_time"] or "") if all(info[f]["creation_time"] for f in files) else None
order = by_time or by_name
print("order by filename :", by_name)
print("order by recording:", by_time if by_time else "(no creation_time tags)")
if by_time and by_time != by_name:
    print("!! filename order and recording-time order DISAGREE. Using recording time; confirm with the transcripts.")

mapping = []
for k, f in enumerate(order):
    n = a.first_slide + k
    mapping.append({"slide": n, "file": os.path.join("input", "recordings", f), **info[f]})
    ff(["-y", "-i", os.path.join(inp, f), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", wp(W, "raw", rec_id(n) + ".wav")], check=True)
save_json(mapping, os.path.join(W, "mapping.json"))
for m in mapping:
    print(f"  slide {m['slide']:2d} <- {os.path.basename(m['file'])}  {m['duration']:6.1f}s  {m['sample_rate']} Hz  {m['creation_time'] or ''}")
low = [m for m in mapping if m["sample_rate"] and int(m["sample_rate"]) < 32000]
if low:
    print(f"note: {len(low)} recordings are below 32 kHz (e.g. {low[0]['sample_rate']} Hz): bandwidth is limited; do not try to 'restore' it "
          "with generative models (see references/audio.md). Suggest Voice Memos > Lossless for future recordings.")

# ---------------------------------------------------------------- deck
slides = []
if a.deck:
    ext = os.path.splitext(a.deck)[1].lower()
    src_copy = wp(W, "deck", "source" + ext)
    shutil.copy2(a.deck, src_copy)
    if ext == ".pptx":
        ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main", "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
              "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
        z = zipfile.ZipFile(src_copy)
        pres = ET.fromstring(z.read("ppt/presentation.xml"))
        rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("ppt/_rels/presentation.xml.rels"))}
        order_xml = [rels[s.get("{%s}id" % ns["r"])] for s in pres.find("p:sldIdLst", ns)]

        def texts(xml):
            out = []
            for p in ET.fromstring(xml).iter("{%s}p" % ns["a"]):
                t = "".join(x.text or "" for x in p.iter("{%s}t" % ns["a"])).strip()
                if t and t != "‹#›" and not re.fullmatch(r"\d+", t):
                    out.append(t)
            return out

        for i, target in enumerate(order_xml, 1):
            path = "ppt/" + target.replace("../", "")
            xml = z.read(path)
            root = ET.fromstring(xml)
            relp = "ppt/slides/_rels/" + os.path.basename(path) + ".rels"
            notes, media = [], []
            if relp in z.namelist():
                for r in ET.fromstring(z.read(relp)):
                    t = r.get("Type")
                    if t.endswith("/notesSlide"):
                        notes = texts(z.read("ppt/" + r.get("Target").replace("../", "")))
                    if t.endswith(("/audio", "/video", "/media")):
                        media.append(r.get("Target"))
            sx = xml.decode("utf8", "ignore")
            slides.append({"n": i, "hidden": root.get("show") == "0", "text": texts(xml), "notes": notes,
                           "animations": sx.count("<p:par>") if "<p:timing" in sx else 0, "media": media})
        # render slides: PowerPoint (Windows) on the COPY, else LibreOffice -> PDF
        out_png = wp(W, "deck")
        rendered = False
        if os.name == "nt" and shutil.which("powershell"):
            ps = os.path.join(SKILL_DIR, "scripts", "export_slides.ps1")
            r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps, "-Pptx", src_copy, "-OutDir", out_png],
                               capture_output=True, text=True)
            print(r.stdout.strip()[-800:])
            rendered = bool(glob.glob(os.path.join(out_png, "slide*.png")))
        if not rendered:
            soffice = shutil.which("soffice") or shutil.which("libreoffice")
            if soffice:
                subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", out_png, src_copy], capture_output=True)
                pdf = os.path.join(out_png, "source.pdf")
                ext, src_copy = ".pdf", pdf
            else:
                print("!! could not render slides: no PowerPoint and no LibreOffice. Install LibreOffice or export PNGs manually to W/deck/slideNN.png")
    if ext == ".pdf" and os.path.exists(src_copy):
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(src_copy)
            for i, page in enumerate(doc, 1):
                z = 1920 / page.rect.width
                page.get_pixmap(matrix=fitz.Matrix(z, z)).save(os.path.join(W, "deck", f"slide{i:02d}.png"))
                if len(slides) < i:
                    slides.append({"n": i, "hidden": False, "text": [l for l in page.get_text().splitlines() if l.strip()], "notes": [], "animations": 0, "media": []})
        except ImportError:
            print("!! pip install pymupdf to render PDF decks")
    save_json(slides, os.path.join(W, "deck", "slides.json"))
    print(f"deck: {len(slides)} slides; rendered {len(glob.glob(os.path.join(W, 'deck', 'slide*.png')))} PNGs")
    flagged = [s["n"] for s in slides if s["animations"] or s["media"]]
    if flagged:
        print(f"!! slides with animations or embedded media: {flagged} (tell the user before flattening them)")
    hidden = [s["n"] for s in slides if s["hidden"]]
    if hidden:
        print(f"hidden slides: {hidden}")
    if len(mapping) < len(slides):
        print(f"{len(slides) - len(mapping)} slides have no recording (often appendix/backup slides): they are left out of the video.")
    if len(mapping) == 1 and len(slides) > 2:
        print("ONE recording for many slides: transcribe it, write W/split_plan.json, run split.py (references/intake.md).")

# ---------------------------------------------------------------- project.json skeleton
pj = os.path.join(W, "project.json")
if not os.path.exists(pj):
    title = slides[0]["text"][0] if slides and slides[0]["text"] else "Talk"
    save_json({
        "short_title": title.split(":")[0][:40],
        "title": title,
        "authors": "",
        "affiliations": [],
        "venue": "",
        "co_located": "",
        "language": "en",
        "palette": {"primary": "#0088C8", "ink": "#181050", "accent": "#58C0E8", "paper": "#F6F4EE", "bad": "#C0283D", "good": "#1E8576"},
        "sections": [],
        "logos": {"top_left": [], "top_right": [], "bottom": []},
        "content_warning": "",
        "content_warning_at": "",
        "output_name": re.sub(r"[^A-Za-z0-9]+", "_", title.split(":")[0]).strip("_")[:40] or "talk",
    }, pj)
    print("wrote project.json skeleton: fill in authors/affiliations (title slide text is in deck/slides.json), venue, "
          "palette (or run palette_from_logo.py), sections, logos (references/project-json.md)")
