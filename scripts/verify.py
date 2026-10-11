"""Automated QA of a delivered MP4: format, frame count vs timeline, loudness, black frames, long silences, clipping,
independent A/V sync (re-transcribe the file and compare anchor words with the timeline), and a mid-scene contact sheet.

usage: python verify.py --work W --video W/delivery/talk_final.mp4 [--no-sync]
Report honestly: these are automated checks plus the contact sheet you look at. Nobody has LISTENED unless the user did.
"""
import json, os, re, subprocess
import numpy as np
from common import args_with_work, wp, load_json, save_json, project, ff, ffprobe, ffmpeg, loudness, norm


def extra(ap):
    ap.add_argument("--video", required=True)
    ap.add_argument("--no-sync", action="store_true")


a = args_with_work(__doc__, extra)
W, V = a.work, a.video
tl = load_json(os.path.join(W, "remotion", "src", "data", "timeline.json"))
pr = subprocess.run([ffprobe(), "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                     "stream=codec_name,width,height,pix_fmt,r_frame_rate,nb_read_packets,color_space", "-of", "json", V], capture_output=True, text=True).stdout
v = json.loads(pr)["streams"][0]
base = os.path.splitext(os.path.basename(V))[0]
res = {"video": V, "codec": v["codec_name"], "size": f"{v['width']}x{v['height']}", "pix_fmt": v["pix_fmt"], "fps": v["r_frame_rate"],
       "frames": int(v["nb_read_packets"]), "timeline_frames": tl["totalFrames"]}
print(f"video: {v['codec_name']} {v['width']}x{v['height']} {v['pix_fmt']} {v['r_frame_rate']} {v.get('color_space')} | frames {v['nb_read_packets']} (timeline {tl['totalFrames']})")
I, LRA, TP = loudness(V)
print(f"audio: {I:.1f} LUFS integrated, LRA {LRA:.1f}, true peak {TP:.1f} dBTP")
res.update(lufs=round(I, 1), lra=round(LRA, 1), true_peak=round(TP, 1))
e = ff(["-i", V, "-vf", "blackdetect=d=0.1:pic_th=0.98", "-an", "-f", "null", "-"])
print("black runs:", e.count("black_start"))
res["black_runs"] = e.count("black_start")
e = ff(["-i", V, "-af", "silencedetect=n=-50dB:d=1.0", "-vn", "-f", "null", "-"])
res["silences_over_1s"] = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", e)]
print("silences > 1 s at:", res["silences_over_1s"], "(the end hold is expected)")
e = ff(["-i", V, "-af", "astats=measure_overall=Peak_count+Flat_factor:measure_perchannel=none", "-vn", "-f", "null", "-"])
res["clipping"] = " ".join(re.findall(r"(Flat factor: [\d.]+|Peak count: [\d.]+)", e))
print("clipping:", res["clipping"])
# contact sheet: one frame from 62% into every scene
from PIL import Image, ImageDraw
sh_dir = wp(W, "out", "verify")
thumbs = []
for s in tl["slides"]:
    t = (s["startFrame"] + s["frames"] * 0.62) / tl["fps"]
    p = os.path.join(sh_dir, f"m{s['n']:02d}.jpg")
    subprocess.run([ffmpeg(), "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", V, "-frames:v", "1", "-vf", "scale=480:-1", p])
    thumbs.append(p)
cols = 4
rows = (len(thumbs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 486, rows * 276), "black")
d = ImageDraw.Draw(sheet)
for k, p in enumerate(thumbs):
    if os.path.exists(p):
        sheet.paste(Image.open(p), ((k % cols) * 486, (k // cols) * 276))
        d.text(((k % cols) * 486 + 4, (k // cols) * 276 + 4), f"slide {tl['slides'][k]['n']}", fill="yellow")
res["sheet"] = os.path.join(W, "out", f"verify_sheet_{base}.jpg")
sheet.save(res["sheet"], quality=88)
print("contact sheet:", res["sheet"], "(look at it)")
if a.no_sync:
    save_json(res, os.path.join(W, "out", f"verify_{base}.json"))
    raise SystemExit
from faster_whisper import WhisperModel
wav = os.path.join(sh_dir, "sync.wav")
subprocess.run([ffmpeg(), "-v", "error", "-y", "-i", V, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
try:
    m = WhisperModel("large-v3", device="cuda", compute_type="float16")
except Exception:
    m = WhisperModel("large-v3", device="cpu", compute_type="int8")
segs, _ = m.transcribe(wav, language=project(W).get("language") or None, beam_size=5, word_timestamps=True, condition_on_previous_text=False, vad_filter=True)
heard = [(norm(w.word), w.start) for s in segs for w in s.words]
errs = []
for s in tl["slides"]:
    st = s["startFrame"] / tl["fps"]
    for w in s["words"][2:5]:
        exp = st + w["s"]
        c = [t for k, t in heard if k == norm(w["w"]) and abs(t - exp) < 3]
        if c:
            errs.append(min(c, key=lambda t: abs(t - exp)) - exp)
errs = np.array(errs)
if len(errs):
    res["sync"] = {"anchors": len(errs), "median_ms": round(float(np.median(errs)) * 1000), "max_abs_ms": round(float(np.max(np.abs(errs))) * 1000)}
    print(f"sync: {len(errs)} anchor words; median {np.median(errs) * 1000:+.0f} ms, mean |err| {np.mean(np.abs(errs)) * 1000:.0f} ms, max {np.max(np.abs(errs)) * 1000:.0f} ms")
else:
    print("sync: no anchor words matched (check the language setting)")
save_json(res, os.path.join(W, "out", f"verify_{base}.json"))
