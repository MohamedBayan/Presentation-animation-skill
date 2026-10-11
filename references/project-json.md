# W/project.json

`ingest.py` writes a skeleton. Fill it from the title slide (`deck/slides.json` slide 1), the user's answers, and official sources. `build_timeline.py` copies it into the Remotion project, so re-run it after edits.

```json
{
 "short_title": "TinyQA",
 "title": "TinyQA: A Compact Benchmark for Fine-Grained Question Answering",
 "authors": "First Author, Second Author, Third Author",
 "affiliations": ["Example University", "Example Research Lab"],
 "venue": "ACL 2026",
 "co_located": "Vienna, Austria",
 "language": "en",
 "palette": {"primary": "#0088C8", "ink": "#181050", "accent": "#58C0E8", "paper": "#F6F4EE", "bad": "#C0283D", "good": "#1E8576"},
 "sections": [{"from": 1, "name": "Introduction"}, {"from": 3, "name": "Dataset"}, {"from": 6, "name": "Experiments"}, {"from": 9, "name": "Conclusion"}],
 "logos": {"top_left": ["logos/university.png"], "top_right": ["logos/lab.png"], "bottom": ["logos/conference.png"]},
 "content_warning": "This talk contains examples of offensive content.",
 "content_warning_at": "offensive",
 "output_name": "TinyQA_ACL2026"
}
```

| Field | Used by | Notes |
|---|---|---|
| `short_title` | title card (big), header on every slide | ≤ 14 characters reads best; the first third is drawn in the primary colour |
| `title` | title card subtitle (the part after `:`), report | |
| `authors` | TitleScene (its presence switches the first slide to TitleScene) | one string; keep the deck's order and spelling |
| `affiliations` | TitleScene | list, one line each |
| `venue` | badge on the title card, header | e.g. "ACL 2026", "NeurIPS 2026" |
| `co_located` | small line next to the venue badge | optional |
| `language` | Whisper language, sync check | "en", "ar", ... (Whisper codes); empty lets Whisper detect it |
| `palette` | `theme.ts`, paper textures, chapter page | see `animation-design.md` §9 |
| `sections` | chapter wipes and the header's section label | `from` is a slide number (the first section usually starts at 1, with no wipe on the first slide); 4–6 sections for a 15-slide talk; empty means no wipes |
| `logos` | TitleScene; custom scenes can use `staticFile('img/logos/<file>')` | paths relative to W or absolute; `make_assets.py` copies them. Only official files: download from the institution's brand or press page, or ask the user. Transparent PNG or SVG-rendered PNG, at least 300 px tall |
| `content_warning` | TitleScene (red bar) | empty means none |
| `content_warning_at` | time the warning appears | a phrase from slide 1; default 1.2 s |
| `output_name` | delivery file names | ASCII, no spaces |
