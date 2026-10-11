"""Contact sheet from a folder of frames (preview.py calls it).
usage: python sheet.py <frames_dir> <out.jpg> [cols=3] [thumb_width=640] [props.json with {"frames":[...]} for labels]
Look at ONE sheet per QA pass instead of many single frames (saves tokens, catches layout bugs fast)."""
import glob, json, re, sys
from PIL import Image, ImageDraw

d, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 3
W = int(sys.argv[4]) if len(sys.argv) > 4 else 640
fr = json.load(open(sys.argv[5]))["frames"] if len(sys.argv) > 5 else None
fs = sorted(glob.glob(d + "/*.jpeg") + glob.glob(d + "/*.jpg") + glob.glob(d + "/*.png"),
            key=lambda f: int((re.findall(r"[0-9]+", f.replace("\\", "/").split("/")[-1]) or ["0"])[-1]))  # element-10 after element-9
H = int(W * 1080 / 1920)
rows = (len(fs) + cols - 1) // cols
sh = Image.new("RGB", (cols * W + (cols - 1) * 6, rows * H + (rows - 1) * 6), "black")
dr = ImageDraw.Draw(sh)
for i, f in enumerate(fs):
    x, y = (i % cols) * (W + 6), (i // cols) * (H + 6)
    sh.paste(Image.open(f).convert("RGB").resize((W, H)), (x, y))
    lab = f"#{i}" + (f" f{fr[i]} {fr[i] / 30:.1f}s" if fr and i < len(fr) else "")
    dr.rectangle([x, y, x + 150, y + 20], fill="black")
    dr.text((x + 4, y + 4), lab, fill="yellow")
sh.save(out, quality=88)
print(out)
