"""Sample a brand palette from a logo and write it into project.json.

usage: python palette_from_logo.py --work W --logo path/to/logo.png
Picks the most frequent saturated colours: primary (most common), ink (darkest), accent (lightest saturated).
Check the result; semantic colours (bad/good) stay as they are.
"""
from collections import Counter
from PIL import Image
from common import args_with_work, project, save_json
import os, colorsys


def extra(ap):
    ap.add_argument("--logo", required=True)


a = args_with_work(__doc__, extra)
im = Image.open(a.logo).convert("RGBA")
im.thumbnail((400, 400))
c = Counter()
for r, g, b, al in im.getdata():
    if al > 250 and not (r > 230 and g > 230 and b > 230):
        c[(r // 8 * 8, g // 8 * 8, b // 8 * 8)] += 1
top = [k for k, _ in c.most_common(12)]
hexs = lambda k: "#%02X%02X%02X" % k
lum = lambda k: colorsys.rgb_to_hls(*[v / 255 for v in k])[1]
sat = lambda k: colorsys.rgb_to_hls(*[v / 255 for v in k])[2]
primary = top[0]
ink = min(top, key=lum)
accent = max([k for k in top if sat(k) > 0.3] or top, key=lum)
P = project(a.work)
P.setdefault("palette", {}).update({"primary": hexs(primary), "ink": hexs(ink), "accent": hexs(accent)})
save_json(P, os.path.join(a.work, "project.json"))
print("palette:", P["palette"])
