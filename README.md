# Presentation animation skill

A Claude Code skill that turns talk recordings (with or without slides) into a finished, conference-ready talk video:

- **Narration editing.** Removes retakes, false starts and dead air. Words are never cut or invented.
- **Conservative voice enhancement**, mastered to -16 LUFS.
- **A Vox-style animated explainer** built in [Remotion](https://www.remotion.dev/): marker highlights, hand-drawn circles and arrows, counters and charts, all timed to the spoken words, with synthesized sound effects and chapter wipes.
- **Small word-synced captions**, plus SRT, transcript, an edit report with timestamps to listen to, and a Remotion Studio project for tweaks.

It was distilled from producing a real conference talk video end to end; the lessons from that run are in `references/lessons-learned.md`.

## Install

```bash
git clone https://github.com/MohamedBayan/Presentation-animation-skill.git ~/.claude/skills/presentation-animation
```

Then ask Claude Code something like *"Here are my recordings and slides for my ACL talk, make the presentation video"*. The skill triggers on requests about talk videos, recordings plus slides, narration cleanup, captions or animated explainers.

## Requirements

`scripts/check_env.py` checks all of these and tells you what is missing:

- Python 3.9+ with `faster-whisper`, `soundfile`, `numpy`, `scipy`, `pillow` (and `pymupdf` for PDF decks)
- ffmpeg
- Node.js 18+ (Remotion 4.0.290 is installed per project)
- Slide rendering: PowerPoint (Windows) or LibreOffice, or a PDF of the deck
- Optional: a CUDA GPU (Whisper large-v3 also runs on CPU, slower)

## Pipeline at a glance

```text
ingest → transcribe → island audit → edit_plan.json → cut → enhance → re-transcribe/audit
       → build_timeline (captions, SRT) → make_assets (Remotion project, SFX, fonts)
       → scenes (fast: slide + cues | no deck: points | full: custom Vox scenes) → preview sheets
       → render (chunks, SFX stem, captions, master, mux, verify) → report
```

## Layout

| Path | What |
|---|---|
| `SKILL.md` | the workflow Claude follows |
| `references/` | detailed guides: intake, narration editing, audio, animation design, render and delivery, project.json, lessons learned |
| `scripts/` | the pipeline (Python; every script takes `--work <folder>`) |
| `assets/remotion-template/` | Remotion project: engine (`Main`, `Root`, captions, primitives, charts, icons) and generic scenes (title, slide + cues, points) |
| `examples/sample-talk/` | a fictional sample talk: project.json, edit plan, corrections, facts log and six full-tier recipe scenes |

Fonts bundled under the SIL Open Font License: Inter, Caveat, Cairo (see `assets/remotion-template/public/fonts/LICENSES.txt`). Sound effects are synthesized by `make_assets.py`; no third-party samples.
