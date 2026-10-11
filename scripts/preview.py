"""Fast visual QA: render chosen frames of the full video (with captions) into one labelled contact sheet.

usage:
  python preview.py --work W --slides                 3 frames per slide (25 %, 60 %, 95 % of its narration)
  python preview.py --work W --slides 4 6             the same, only slides 4 and 6
  python preview.py --work W --frames 120 900 1500    exact global frames
  python preview.py --work W --at 4:publicly 6:"error analysis"   the frame where a phrase is spoken (+0.8 s)
Writes W/out/preview/<name>_sheet.jpg (look at it with your image viewer tool) and the single frames next to it.
Renders the Preview composition: <Freeze>s Main at each requested frame, so 12 frames take seconds, not minutes.
"""
import json, os, shutil, subprocess, sys
from common import args_with_work, wp, load_json, norm

HERE = os.path.dirname(os.path.abspath(__file__))


def extra(ap):
    ap.add_argument("--slides", nargs="*", type=int)
    ap.add_argument("--frames", nargs="*", type=int)
    ap.add_argument("--at", nargs="*", help="slide:phrase")
    ap.add_argument("--name", default="sheet")
    ap.add_argument("--no-captions", action="store_true")
    ap.add_argument("--cols", type=int, default=3)


a = args_with_work(__doc__, extra)
W = a.work
R = os.path.join(W, "remotion")
tl = load_json(os.path.join(R, "src", "data", "timeline.json"))
fps = tl["fps"]
by_n = {s["n"]: s for s in tl["slides"]}
frames = list(a.frames or [])
if a.slides is not None:
    for s in tl["slides"]:
        if not a.slides or s["n"] in a.slides:
            frames += [s["startFrame"] + int(s["frames"] * p) for p in (0.25, 0.6, 0.95)]
for spec in a.at or []:
    n, phrase = spec.split(":", 1)
    s = by_n[int(n)]
    target = norm(phrase)
    ws = [w for w in s["words"] if norm(w["w"])]
    hit = None
    for i in range(len(ws)):
        acc = ""
        for j in range(i, len(ws)):
            acc += norm(ws[j]["w"])
            if len(acc) >= len(target):
                break
        if acc == target:
            hit = ws[i]["s"]
            break
    if hit is None:
        print(f"!! phrase not found on slide {n}: {phrase}")
        continue
    frames.append(s["startFrame"] + int((hit + 0.8) * fps))
frames = [max(0, min(tl["totalFrames"] - 1, f)) for f in frames]
if not frames:
    sys.exit("nothing to render: pass --slides, --frames or --at")
od = wp(W, "out", "preview", a.name)
shutil.rmtree(od, ignore_errors=True)
props = os.path.join(wp(W, "out", "preview"), a.name + "_props.json")
json.dump({"frames": frames, "captions": not a.no_captions}, open(props, "w"))
npx = shutil.which("npx") or shutil.which("npx.cmd")
r = subprocess.run([npx, "remotion", "render", "src/index.ts", "Preview", od, "--sequence", "--image-format=jpeg", f"--props={props}",
                    f"--frames=0-{len(frames) - 1}", "--timeout=90000", "--log=error"], cwd=R, capture_output=True, text=True, errors="replace")
if r.returncode:
    print(r.stdout[-1500:], r.stderr[-1500:])
    sys.exit("preview render failed (a phrase cue that is not spoken, or a TypeScript error, are the usual causes)")
sheet = os.path.join(W, "out", "preview", a.name + "_sheet.jpg")
subprocess.run([sys.executable, os.path.join(HERE, "sheet.py"), od, sheet, str(a.cols), "640", props], check=True)
print("sheet:", sheet, "| frames:", frames)
