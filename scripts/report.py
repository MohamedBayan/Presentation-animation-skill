"""Draft W/delivery/EDIT_REPORT.md from the pipeline's own records, so every number in it is real.

usage: python report.py --work W
Reads project.json, mapping.json, edit_plan.json, cut/*_map.json, cut/cut_log.md, clean/loudness_stats.json,
corrections.json, out/verify_*.json and the timeline. Every explicit cut is listed with its time in the FINAL video, so the
user can jump there and listen. Cuts whose reason contains "FLAG" and joins louder than -50 dBFS go into a "please listen"
list. Afterwards, edit the draft by hand: add the narrative (what you changed and why, anything the user asked for).
"""
import glob, os, re
from common import args_with_work, load_json, project

a = args_with_work(__doc__)
W = a.work
P = project(W)
name = P.get("output_name", "talk")
tl = load_json(os.path.join(W, "remotion", "src", "data", "timeline.json"))
fps = tl["fps"]
start = {s["n"]: s["startFrame"] / fps for s in tl["slides"]}
mapping = {m["slide"]: m for m in load_json(os.path.join(W, "mapping.json"), [])}
plan = load_json(os.path.join(W, "edit_plan.json"), {"recordings": {}})
loud = load_json(os.path.join(W, "clean", "loudness_stats.json"), {})
corr = load_json(os.path.join(W, "corrections.json"), [])
log = open(os.path.join(W, "cut", "cut_log.md"), encoding="utf8").read() if os.path.exists(os.path.join(W, "cut", "cut_log.md")) else ""


def mmss(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def to_new(cmap, t):
    """original-recording time -> edited-clip time (the next kept piece after t)"""
    for k in cmap["keep"]:
        if k["orig_end"] >= t:
            return k["new_start"] + max(0.0, t - k["orig_start"])
    return cmap["new_dur"]


L = [f"# {P.get('title', name)}: edit report\n"]
L.append("| Deliverable | What it is |\n|---|---|")
desc = {"_final.mp4": "Main video: animated, small burned-in captions, 1920x1080 30 fps H.264 + AAC",
        "_final_no_captions.mp4": "The same video without burned-in captions", "_slides_version.mp4": "Plain slides version, same narration",
        ".srt": "Subtitles for the animated video", "_slides_version.srt": "Subtitles for the slides version", "_transcript.md": "Transcript by slide with timecodes"}
for f in sorted(os.listdir(os.path.join(W, "delivery"))):
    d = next((v for k, v in sorted(desc.items(), key=lambda kv: -len(kv[0])) if f.endswith(k)), "")
    if f != "EDIT_REPORT.md":
        L.append(f"| `{f}` | {d} |")

rows, cuts, listen = [], [], []
tot_o = tot_n = 0.0
for s in tl["slides"]:
    rec = f"rec{s['n']:02d}"
    cm = load_json(os.path.join(W, "cut", rec + "_map.json"))
    if not cm:
        continue
    removes = plan.get("recordings", {}).get(rec, {}).get("remove", [])
    src = os.path.basename(mapping.get(s["n"], {}).get("file", rec))
    rows.append(f"| {s['n']} | {src} | {cm['orig_dur']:.1f} | {cm['new_dur']:.1f} | {cm['orig_dur'] - cm['new_dur']:.1f} | {len(removes)} | {mmss(start[s['n']])} |")
    tot_o += cm["orig_dur"]
    tot_n += cm["new_dur"]
    for r in removes:
        t = start[s["n"]] + to_new(cm, r["end"])
        cuts.append(f"| {s['n']} | {mmss(t)} | {r['start']:.2f}-{r['end']:.2f} | {r.get('reason', '')} |")
        if "FLAG" in r.get("reason", "").upper():
            listen.append(f"- slide {s['n']}, video {mmss(t)}: {r.get('reason', '')}")
    m = re.search(rf"## {rec},.*?loudest 10 ms frame at a join = (-?\d+) dBFS", log, re.S)
    if m and int(m.group(1)) > -50:
        listen.append(f"- slide {s['n']}: a join peaks at {m.group(1)} dBFS (above the -50 dBFS target); listen to its cuts")

L.append("\n## 1. Narration editing\n")
L.append("Every recording was transcribed as a whole and, to catch retakes that whole-file ASR merges, island by island. "
         "Explicit cuts (retakes, false starts, self-corrections, dead air) are listed below with the time where the join "
         "lands in the final video. Each cut edge snaps to the quietest 10 ms nearby, and every join is a 12 ms crossfade.")
d = {**{"gap_sentence": 0.42, "gap_comma": 0.28, "gap_word": 0.18, "lead_in": 0.25, "tail": 0.35, "gap_thr": -50}, **plan.get("defaults", {})}
L.append(f"Pauses are capped by context: {d['gap_sentence']} s between sentences, {d['gap_comma']} s after a comma, "
         f"{d['gap_word']} s inside a sentence. Silence means below {d['gap_thr']} dBFS, so breaths and quiet consonants stay. "
         f"Each slide starts {d['lead_in']} s before its first word and ends {d['tail']} s after its last.\n")
if cuts:
    L.append("| Slide | Final video at | Original (s) | What was removed and why |\n|---|---|---|---|")
    L += cuts
L.append("\n| Slide | Recording | Original (s) | Edited (s) | Removed (s) | Explicit cuts | Starts at |\n|---|---|---|---|---|---|---|")
L += rows
L.append(f"| **Total** | | **{tot_o:.1f}** ({tot_o / 60:.1f} min) | **{tot_n:.1f}** ({tot_n / 60:.1f} min) | **{tot_o - tot_n:.1f}** | | |")
L.append("\n### Please listen to these spots\n")
L += listen or ["- none flagged by the automated checks; the cut list above has every join if you want to spot-check"]

L.append("\n## 2. Audio\n")
L.append("Conservative chain on each clip: resample to 48 kHz (soxr), 80 Hz high-pass, -2 dB at 300 Hz, +2 dB at 2.6 kHz, "
         "gentle 2:1 compression above -22 dBFS, static gain to the loudness target, 4x-oversampled limiter at -2 dBFS. "
         "No denoiser, no bandwidth \"restoration\" (generative upsampling made the voice sound artificial in testing). "
         "Sound effects sit about 15 dB under the voice.\n")
if loud:
    L.append("| Clip | LUFS | True peak | LRA | Limiter active |\n|---|---|---|---|---|")
    L += [f"| {k} | {v['I']} | {v['TP']} | {v['LRA']} | {v.get('limited_pct', 0)} % |" for k, v in sorted(loud.items())]

L.append("\n## 3. Automated QA\n")
for f in sorted(glob.glob(os.path.join(W, "out", "verify_*.json"))):
    v = load_json(f)
    sync = v.get("sync")
    L.append(f"- `{os.path.basename(v['video'])}`: {v['codec']} {v['size']} {v['fps']} {v['pix_fmt']}, {v['frames']} frames "
             f"(timeline {v['timeline_frames']}); {v['lufs']} LUFS, true peak {v['true_peak']} dBTP; black runs {v['black_runs']}; "
             f"silences over 1 s at {', '.join(mmss(x) for x in v['silences_over_1s']) or 'none'}" + (f"; A/V sync on {sync['anchors']} re-transcribed anchor words: median "
             f"{sync['median_ms']:+d} ms, worst {sync['max_abs_ms']} ms" if sync else ""))
L.append("\nThese are automated measurements (ASR, loudness, levels at the joins, frame checks) plus contact sheets I looked at. "
         "I cannot listen. Please give the video one full listen before you submit it.")
if corr:
    L.append("\n## 4. Caption fixes (text only, audio unchanged)\n")
    L += [f"- \"{h}\" → \"{c}\"" for h, c in corr]
out = os.path.join(W, "delivery", "EDIT_REPORT.md")
open(out, "w", encoding="utf8").write("\n".join(L) + "\n")
print("draft report ->", out)
