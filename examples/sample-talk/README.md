# Sample talk (fictional)

A made-up 10-slide talk, "TinyQA", showing what the per-talk files look like and how full-tier scenes are written. All names, numbers and phrases are placeholders. Never copy them into a real video.

| File | What it shows |
|---|---|
| `project.json` | talk metadata, palette, sections and logo slots (`references/project-json.md`) |
| `edit_plan.json` | the cut list format, with one cut of each kind (false start, retake, dead air, self-correction, flagged in-speech cut). Copy the reason style: `report.py` puts these reasons in front of the user |
| `corrections.json` | ASR fixes applied to captions and SRT only (never to audio) |
| `facts.md` | the on-screen facts log to keep for every talk |
| `scenes/Recipes.tsx` | six full-tier scenes: `Contribution` (row of big counted numbers), `RelatedWork` (table rebuilt row by row, own row last), `FigureWalkthrough` (deck figure with regions in spoken order), `MainResult` (bars, focus on the best, delta), `Takeaways` (numbered cards + "Next"), `Thanks` (dark page, contact, QR card) |

To use a recipe:

1. Copy it into `W/remotion/src/scenes/` and register it in `CUSTOM` in `src/scenes/index.ts` under its slide number.
2. Replace every `at('...')` phrase with a phrase spoken on that slide; the cut-stage transcript is in `W/transcripts/cut/recNN.txt`.
3. Replace all data with the deck's values, and log each one in `W/facts.md`.
4. Check it with `preview.py --slides N`.

Recipes import `../theme`, `../lib`, `../icons` and `../charts` from the template, so they compile as-is inside a project.
