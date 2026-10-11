"""Final encode: Remotion picture [+ transparent caption layer] + mastered audio -> delivery MP4.

usage: python mux.py --work W [--captions] [--name custom.mp4]
Inputs: W/out/video_noaudio.mp4 (joined render chunks), W/out/mix_master.wav, W/out/caps/cap_%05d.png (with --captions).
Remotion emits full-range BT.601 (yuvj420p); compositing happens in RGB and the output is standard limited-range BT.709
yuv420p, x264 CRF 16 (slow, tune animation), AAC-LC 192 kb/s 48 kHz stereo, +faststart, trimmed to the exact timeline length.
"""
import os
from common import args_with_work, wp, load_json, project, ff, loudness


def extra(ap):
    ap.add_argument("--captions", action="store_true")
    ap.add_argument("--name")


a = args_with_work(__doc__, extra)
W = a.work
P = project(W)
tl = load_json(os.path.join(W, "remotion", "src", "data", "timeline.json"))
name = a.name or (P.get("output_name", "talk") + ("_final.mp4" if a.captions else "_final_no_captions.mp4"))
out = os.path.join(wp(W, "delivery"), name)
vid = os.path.join(wp(W, "out"), "video_noaudio.mp4")
lst = os.path.join(W, "remotion", "out", "chunks", "list.txt")   # written by render_chunks.sh
if os.path.exists(lst) and (not os.path.exists(vid) or os.path.getmtime(lst) > os.path.getmtime(vid)):
    ff(["-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)
    print("joined render chunks ->", vid)
FL = "flags=accurate_rnd+full_chroma_int"
args = ["-y", "-i", vid, "-i", os.path.join(W, "out", "mix_master.wav")]
if a.captions:
    args += ["-framerate", str(tl["fps"]), "-start_number", "0", "-i", os.path.join(W, "out", "caps", "cap_%05d.png")]
    fc = (f"[0:v]scale=in_color_matrix=bt601:in_range=full:{FL},format=gbrp[b];[2:v]format=gbrap[o];"
          f"[b][o]overlay=format=gbrp:eof_action=pass,scale=out_color_matrix=bt709:out_range=tv:{FL},format=yuv420p[v]")
else:
    fc = f"[0:v]scale=in_color_matrix=bt601:out_color_matrix=bt709:in_range=full:out_range=tv:{FL},format=yuv420p[v]"
args += ["-filter_complex", fc, "-map", "[v]", "-map", "1:a:0", "-frames:v", str(tl["totalFrames"]),
         "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-tune", "animation", "-profile:v", "high", "-level", "4.1",
         "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", "-r", str(tl["fps"]),
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", out]
ff(args, check=True)
I, LRA, TP = loudness(out)
print(f"{out}: {I:.1f} LUFS, true peak {TP:.1f} dBTP")
