---
name: presentation-animation
description: Turns talk recordings (one clip per slide or one long take), with or without the slide deck (.pptx or .pdf), into a finished conference talk video. Edits the narration (removes retakes, false starts and dead air without cutting words), enhances and masters the audio to -16 LUFS, and builds a Vox-style animated explainer in Remotion with sound effects and small word-synced captions, plus SRT, transcript, edit report and a Studio project for tweaks. Use it whenever someone hands over voice memos or recordings and/or slides and wants a presentation video, a pre-recorded conference talk (ACL, NeurIPS, CVPR, ICML...), an animated paper explainer, narration cleanup, captions, or a Remotion talk video, even if they only say "make a video from my recordings" or "turn my talk into a video".
---

# Presentation animation

Recordings (+ slides) in, a conference-ready talk video out. The speaker's real voice is the spine of the video.
Edit it but never rewrite it, and time every animation to the words.

## What you deliver (W/delivery/)

- `<name>_final.mp4`: 1920x1080, 30 fps, H.264 + AAC, -16 LUFS, with small burned-in captions.
- `<name>_final_no_captions.mp4`, and optionally `<name>_slides_version.mp4` (plain slides, same narration).
- `<name>.srt`, `<name>_transcript.md`, and the cleaned WAV per slide.
- `EDIT_REPORT.md`: every cut with its time in the final video, flagged spots to listen to, loudness and QA results.
- The Remotion project (`W/remotion`). The user can open its timeline UI with `npx remotion studio`, adjust things and re-render.

## Ground rules, and why they exist

- **The voice is the user's.** Never synthesize speech or insert words, and never cut inside a word or drop breaths and quiet consonants.
  - Removing a retake is editing; rewording is not. If a fix would need a word that was never said, flag it.
- **Be honest about verification.** You cannot listen.
  - Call your checks what they are: ASR, levels at the joins, loudness, frames. Give the user exact timestamps to listen to.
- **Originals stay untouched.** `ingest.py` copies everything into `W/input`.
- **PowerPoint safety.** Export from a copy. Never close or quit presentations the user has open: an earlier run discarded a user's unsaved edits.
- **Logos and figures only from official files or the user.** Never redraw or invent a logo.
  - If you can't find one, ask for the file and leave the slot empty meanwhile. `project.json` logos are picked up automatically.
- **On-screen facts come only from the deck or the narration.** Keep `W/facts.md` mapping each number or label to its source (template in `examples/sample-talk/facts.md`).
- **Audio stays conservative** (`references/audio.md`). Bandwidth "restoration" (SBR, AI super-resolution) made a phone voice sound worse, and the user rejected it.

## Setup (once per machine)

```bash
python <skill>/scripts/check_env.py
```

It checks ffmpeg, faster-whisper, Node, PowerPoint or LibreOffice, and CUDA. When the current Python lacks the packages, it lists the interpreters that have them. Use that interpreter as `$PY` for every script. Install anything missing yourself and don't hand it to the user. Remotion and its headless Chrome are installed per project by `make_assets.py --install`.

## Pipeline

`S` = this skill's `scripts/`, and `W` = a new work folder next to the user's files (e.g. `<talk>_video/`). Every script takes `--work W`, prints what it did, and can be re-run.

| # | Step | Command | You decide / check |
|---|---|---|---|
| 1 | Intake | `$PY $S/ingest.py --work W --recordings <zip, dir or files> [--deck talk.pptx\|.pdf] [--first-slide N]` | The printed slide↔recording mapping. Fill `W/project.json` (`references/project-json.md`). One long take or no deck: `references/intake.md` |
| 2 | Transcribe | `$PY $S/transcribe.py --work W --stage raw` | |
| 3 | Audit | `$PY $S/audit.py --work W --stage raw` | Read `W/audit/raw_recNN.txt`. Write the removes into `W/edit_plan.json` (`references/narration-editing.md`). Use `probe.py` for borderline cuts |
| 4 | Cut + enhance | `$PY $S/cut.py --work W` then `$PY $S/enhance.py --work W` | Join levels in `W/cut/cut_log.md` (target < -50 dBFS) |
| 5 | Re-check | `transcribe.py --stage cut`, then `audit.py --stage cut` | Repeat 3–5 until no real REPEAT, ECHO or FRAGMENT is left |
| 6 | Timeline | Write `W/corrections.json` (ASR errors in captions), then `$PY $S/build_timeline.py --work W --static` | Read the SRT once for misheard terms |
| 7 | Assets | `$PY $S/make_assets.py --work W --install` | Re-run after re-cuts or logo changes (it never touches your scenes) |
| 8 | Animate | See "Animation tiers" below. QA with `$PY $S/preview.py --work W --slides` and look at the sheet | `references/animation-design.md` |
| 9 | Render | `$PY $S/render.py --work W --fresh` | Picture chunks → SFX stem → captions → master → 2 MP4s → verify. Look at `W/out/verify_sheet_*.jpg` |
| 10 | Report | `$PY $S/report.py --work W`, then edit the draft. Optionally `$PY $S/slides_video.py --work W` | `references/render-and-deliver.md` (hand-off message, Studio, change requests) |

Work in parallel where you can. Steps 2–7 are CPU/GPU-bound scripts, so use their run time to write `project.json`, `facts.md` and scene plans. While waiting for logos or answers, keep working; never block on them.

## Animation tiers

Every slide gets a scene, chosen in this order (`src/scenes/index.ts`):

1. **Custom scene** in `CUSTOM` (full tier). A hand-built Vox-style explainer that rebuilds charts, tables and pipelines as animated graphics, with marker highlights, hand-drawn circles and arrows, counters and stamps, all cued by spoken phrases. Budget about 5–10 minutes of scene work per slide. Start from `examples/sample-talk/scenes/Recipes.tsx` and the primitives in `references/animation-design.md`.
2. **TitleScene** for the first slide when `project.json` has `authors`: an animated title card with logos, venue badge and content warning.
3. **PointsScene** when `src/data/slide_points.json` has an entry: a re-typeset kicker, title, points, a big counted number, a stamp and a note. It's the default when there is no deck.
4. **SlideScene** when the deck gave an image: the rendered slide plus cues from `src/data/slide_cues.json` (zoom, box, circle, mark, note) timed to spoken phrases (fast tier).

How to choose:

- **Requests for "animated", "Vox", "explainer" or "engaging"**: use the full tier for content slides and generic scenes for the title and the thanks slide.
- **"Just make a video of my slides"**, or a tight deadline: use the fast tier (cues on every slide), which takes about 30 minutes for 15 slides.
- **Mixing tiers**: allowed. Upgrade the 3–5 key slides (main result, dataset, method) to custom scenes first.

Ask which tier only when the request doesn't make it clear.

## Talking to the user

- **At the start**, send one short message listing only what's missing:
  - venue and authors if they aren't in the deck;
  - logo files (or official sources);
  - a content warning if the talk shows sensitive material;
  - brand colours (QCRI-like blue/navy is the default; `palette_from_logo.py` samples a logo);
  - captions yes or no (default yes, small).
  Start the audio work while waiting for answers.
- **At delivery**:
  - give the file paths;
  - list the spots to listen to with video timestamps;
  - say what was automated and what wasn't;
  - explain how to open the Studio and re-render;
  - mention anything left open, such as a missing logo.
- **After feedback**, change the smallest thing and re-run only the stages it affects (table in `references/render-and-deliver.md`). After any timing change, the mastered track must be rebuilt (`render.py` does it); otherwise the Studio preview drifts out of sync.

## References (read when you reach that step)

- `references/intake.md`: recordings ↔ slides mapping, one long recording (`split.py`), no deck, video files, builds and embedded media.
- `references/narration-editing.md`: how to find and cut retakes and false starts, cut-point rules, `edit_plan.json` reasons, `probe.py`.
- `references/audio.md`: the enhancement chain, loudness targets, what was tried and rejected, A/B options.
- `references/animation-design.md`: Vox-style principles, layout grid, primitives API, phrase cues, SFX, scene recipes, palette.
- `references/render-and-deliver.md`: render stages, Studio, sync, QA, report, change-request table.
- `references/project-json.md`: every `project.json` field.
- `references/lessons-learned.md`: failures from real runs and their fixes. Skim it before the first render.
