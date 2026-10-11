"""Shared helpers for the presentation-animation pipeline.

Every script takes `--work <dir>` (the per-talk working folder). Layout inside it:
  project.json            talk metadata, palette, sections, logos (see references/project-json.md)
  mapping.json            slide number -> recording file (made by ingest.py, verify it)
  input/                  copies of the user's files (originals are never modified)
  raw/recNN.wav           16 kHz mono decode of each recording (NN = slide number)
  deck/slides.json        slide text + speaker notes, deck/slideNN.png rendered slides
  transcripts/raw|cut/    word-timestamped transcripts (JSON + TXT)
  audit/                  per-island transcription audits
  edit_plan.json          the cut list you write (original-recording seconds)
  cut/recNN.wav           edited narration (+ recNN_map.json, cut_log.md)
  clean/recNN.wav         enhanced narration, 48 kHz 24-bit, -16 LUFS
  corrections.json        ASR fixes for captions/SRT: [["heard words", "correct words"], ...]
  remotion/               the Remotion project (copied from assets/remotion-template)
  out/                    renders, stems, QA sheets
  delivery/               final files for the user
"""
import argparse, glob, json, os, re, shutil, subprocess, sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Windows consoles default to cp1252: printing a transcript with Arabic or a superscript would crash the script.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)  # line-buffered: logs stay in order
    except Exception:
        pass


def args_with_work(desc, extra=None):
    ap = argparse.ArgumentParser(description=desc)
    ap.add_argument("--work", required=True, help="per-talk working folder")
    if extra:
        extra(ap)
    a = ap.parse_args()
    a.work = os.path.abspath(a.work)
    return a


def wp(work, *parts):
    p = os.path.join(work, *parts)
    os.makedirs(os.path.dirname(p) if os.path.splitext(p)[1] else p, exist_ok=True)
    return p


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    return json.load(open(path, encoding="utf8"))


def save_json(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, "w", encoding="utf8"), ensure_ascii=False, indent=1)


def project(work):
    return load_json(os.path.join(work, "project.json"), {})


def rec_id(n):
    return f"rec{int(n):02d}"


# ------------------------------------------------------------------ ffmpeg discovery
def _find_tool(name):
    env = os.environ.get("FFMPEG_DIR")
    if env and os.path.exists(os.path.join(env, name + (".exe" if os.name == "nt" else ""))):
        return os.path.join(env, name + (".exe" if os.name == "nt" else ""))
    w = shutil.which(name)
    if w:
        return w
    if os.name == "nt":  # winget installs Gyan.FFmpeg here without always fixing PATH for the current shell
        hits = glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\**\bin\%s.exe" % name), recursive=True)
        if hits:
            return sorted(hits)[-1]
    sys.exit(f"{name} not found. Install ffmpeg (Windows: winget install Gyan.FFmpeg; macOS: brew install ffmpeg; Linux: apt install ffmpeg) or set FFMPEG_DIR.")


FFMPEG = None
FFPROBE = None


def ffmpeg():
    global FFMPEG
    FFMPEG = FFMPEG or _find_tool("ffmpeg")
    return FFMPEG


def ffprobe():
    global FFPROBE
    FFPROBE = FFPROBE or _find_tool("ffprobe")
    return FFPROBE


def ff(args, check=False):
    r = subprocess.run([ffmpeg(), "-hide_banner", "-nostats"] + args, capture_output=True, text=True)
    if check and r.returncode:
        sys.exit(r.stderr[-3000:])
    return r.stderr


def loudness(path):
    """(integrated LUFS, LRA, true peak dBTP) via ffmpeg ebur128"""
    e = ff(["-i", path, "-af", "ebur128=peak=true:framelog=quiet", "-vn", "-f", "null", "-"])
    g = lambda k: float(re.search(k + r":\s+(-?[\d.]+|-inf)", e).group(1).replace("-inf", "-200"))
    return g("I"), g("LRA"), g("Peak")


def duration(path):
    out = subprocess.run([ffprobe(), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    return float(out.strip() or 0)


# ------------------------------------------------------------------ words / text
def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def words_of(transcript_json):
    """flatten a transcript JSON (list of segments with words) into [{w,s,e,p}]"""
    out = []
    for seg in load_json(transcript_json, []):
        for w in seg.get("words", []):
            out.append({"w": w["w"].strip(), "s": w["s"], "e": w["e"], "p": w.get("p", 1)})
    return out


def join_split_tokens(words):
    """Whisper splits 'Tiny-QA' -> 'Tiny' + '-QA', '12,000' -> '12' + ',000', '37%' -> '37' + '%'. Re-join them."""
    out = []
    for w in words:
        tok = w["w"].strip()
        if out and (tok.startswith(("-", ",", "%")) or (tok.startswith(".") and len(tok) > 1)):
            out[-1]["w"] += tok
            out[-1]["e"] = w["e"]
        else:
            out.append(dict(w, w=tok))
    return out


def apply_corrections(words, corrections):
    """corrections: [[heard, correct], ...] matched case/punctuation-insensitively on word sequences; timings kept."""
    subs = [([norm(t) for t in a.split() if norm(t)], b) for a, b in corrections]
    out, i = [], 0
    nk = lambda x: re.sub(r"[^\w%.-]", "", x.lower()).strip(".")
    while i < len(words):
        hit = None
        for pat, rep in subs:
            n = len(pat)
            if n and [norm(x["w"]) for x in words[i:i + n]] == pat:
                hit = (n, rep)
                break
        if hit:
            n, rep = hit
            last = words[i + n - 1]["w"]
            trail = re.match(r".*?([.,?!]*)$", last).group(1) if not rep.endswith((".", ",", "?", "!")) else ""
            toks = rep.split()
            for k, t in enumerate(toks):
                src = words[min(i + k, i + n - 1)]
                out.append({"w": t + (trail if k == len(toks) - 1 else ""), "s": words[i]["s"] if k == 0 else src["s"],
                            "e": words[i + n - 1]["e"] if k == len(toks) - 1 else src["e"]})
            i += n
        else:
            out.append(words[i])
            i += 1
    return out


def natural_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]
