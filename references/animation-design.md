# Animation design (Remotion)

## Contents
1. Style principles
2. Layout grid
3. Timing to speech
4. Primitives API
5. Sound effects
6. Scene recipes
7. Writing a custom scene
8. Generic scenes: slide_cues.json and slide_points.json
9. Palette and fonts
10. QA loop

## 1. Style principles (Vox-style explainer, conference-appropriate)

- **Things appear when they are said.** Each element is cued to the spoken phrase that introduces it, landing 0.1–0.2 s before the word. Nothing appears early, and the slide's last element lands at least 1 s before the slide ends.
- **One idea per beat.** At most about 3 new elements per spoken sentence. Use focus to point at things rather than pile them up: dim the rest, circle the item, zoom.
- **Rebuild, don't screenshot.**
  - Charts, tables, numbers and lists become live components: bars grow, counters count, rows rise.
  - Use deck images only for figures too complex to rebuild (pipeline diagrams, photos, example inputs or screenshots), and then annotate them (boxes, arrows, notes).
- **A paper-and-marker look.**
  - Paper-textured background, a navy ink, one primary colour, one accent, and semantic red (bad) and green (good).
  - A hand-drawn layer (Caveat font): circles, arrows, short notes and highlighter sweeps.
  - No 3D, no spinning, no bouncy overshoot. Ease-out entrances of 0.35–0.45 s, staggered 0.06–0.12 s.
- **Short text on screen.** Titles of at most 8 words; labels, not sentences. The narration and captions carry the sentences.
- **Every on-screen fact has a source** in the deck or the narration. Write it into `W/facts.md` as you build. Never round differently from the deck, never add a number the speaker didn't give, and never invent example data.
- **Sensitive material.** Keep the content warning on the title card (`project.json` `content_warning`). Show only examples the deck itself shows, at the deck's size or smaller.

## 2. Layout grid (1920×1080)

| Zone | y range | Notes |
|---|---|---|
| Chrome header | 30–60 | short title, venue, section (`Main.tsx`, automatic) |
| `<Header>` kicker + title | 96–230 | `<Header kicker="Results" title="Fusion helps a little" />` |
| Content | 260–940 | side margins 120 px (x 120–1800) |
| Captions | 960–1020 | small pill, bottom centre: keep important content above 940 |
| Progress bar, slide n/N | 1008–1044 | automatic |

Typical columns are 4 × 435 px (x = 120, 555, 990, 1425) or 2 × 820 px (x = 120, 980). Use `<At x y w>` for absolute placement and flex inside it.

## 3. Timing to speech

- `useScene()` returns `{t, dur, n, words}`.
  - `t` is seconds since this slide's narration started; it's negative during the incoming transition.
  - `words` holds the cut-stage Whisper words of this slide, with times.
- `const at = useAt(); at('macro F1')` gives the time the phrase starts, and `at('the best', 1)` the second occurrence.
  - Matching ignores case, punctuation and token splits, so `'12,000'` matches Whisper's `12` `,000`.
  - Choose short phrases that occur once on the slide. A missing phrase throws, and the render fails loudly; that's intended, so a mistimed cue never ships silently. `preview.py` shows the error.
- Re-transcribing after a re-cut can change tokens ("details" became "detail"; "5000" became "5" ",000"). Prefer distinctive content words over function words, and re-run `preview.py --slides` after every re-cut.
- Lead times: `Rise at={at('accuracy') - 0.1}`. For counters, start about 0.1 s before the number is spoken so it lands on the word.
- Transitions: 0.6 s horizontal push with motion blur between slides, and a full-screen chapter wipe ("02 Dataset") where `project.json` `sections` change. Both come with a whoosh, automatically.

## 4. Primitives API (`src/lib.tsx`, `src/charts.tsx`, `src/icons.tsx`)

All times are scene seconds. Primitives marked ♪ bring their own SFX at their cue time; pass `sfx={false}` to silence one.

| Primitive | Props | Use |
|---|---|---|
| `Rise` | `at, out?, d?=0.4, dy?=26, dx?, from?=0.96, style` | fade + rise + slight scale in; the workhorse |
| `At` | `x, y, w?, h?, style` | absolute box |
| `Header` | `kicker, title, at?=0.15, size?=62` | kicker line + title, words rise in sequence |
| `Card` | `style, tape?` | white paper card with a soft shadow (tape strip optional) |
| `Mark` ♪ | `at, color?, strong?` | highlighter sweep behind inline text |
| `HandCircle` ♪ | `x, y, w, h, at, color?, sw?, seed?, out?` | hand-drawn ellipse around a region |
| `HandArrow` ♪ | `x1, y1, x2, y2, at, bend?=0.25, color?, sw?` | hand-drawn curved arrow; `bend` is a fraction of the length (negative curves the other way), not pixels |
| `HandPath` ♪ | `d, at, len?, color?, sw?, dur?, dash?` | any SVG path drawing itself on (underline, bracket) |
| `Note` ♪ | `at, x, y, size?, color?, rot?, w?` | handwritten note that writes itself left to right |
| `Counter` ♪ | `at, to, from?, d?, dec?, prefix?, suffix?, comma?` | number counting up (wrap it in a big-font `Rise`) |
| `Stamp` ♪ | `at, color, size?, rot?, fill?` | rubber-stamp verdict ("BEST", "NOT HUMAN-VERIFIED") |
| `Chip` ♪ | `at, color?, bg?, size?, icon?, out?` | pill label (categories, model names) |
| `FocusBox` ♪ | `x, y, w, h, at, out?, color?, fill?, r?, sw?` | rectangle that pops around a region |
| `Sfx` | `at, name, vol?` | a sound at a time |
| `HBars` (charts) | `rows[{label,value,color,group?,tag?}], at, x, y, w, labelW, min, max, stagger?, dec?, focus?, axis?` | horizontal bar chart that grows; `focus=[{at, keep:[i…]}]` dims the other rows; `barLayout()` returns the bar geometry for annotations |
| `Legend` | `items, at, x, y` | colour legend |
| Icons | `IPerson, IText, IImage, ITarget, IGlobe, IWarn, ICheck, ICross, IUnlock, ISpark, IFusion, IChat, ILock, ISearch, IStack, IPost` with `size, color` | line icons in the ink style |
| helpers | `prog(t, t0, d, ease)`, `vis(t, t0, t1)`, `lerp`, `clamp01`, `EOUT`, `EINOUT`, `fmt(v, dec)` | custom motion |

## 5. Sound effects

`make_assets.py` synthesizes the bank (no third-party samples): `whoosh, whoosh_soft, swish, thud, stamp, pop, pop_lo, tap, tick, counter, marker, pencil, scribble, paper, riser, chime`.

- Primitives and transitions already carry their sounds. Add `<Sfx>` only for moments without a primitive: `thud` when a title lands, `paper` when a card appears, `riser` and `chime` before and on the key result.
- Volumes: 0.03–0.06 for small marks (marker, pencil, pop), 0.08–0.13 for accents (thud, stamp). The stem is peak-normalized to -17.5 dBFS in `master_mix.py`, so relative levels are what matter.
- Density: roughly one sound per 1–2 s of speech. More turns busy, fewer turns dull. On a real 6-minute talk the user asked for "more sound effects to make it engaging", and about 90 explicit cues (plus the primitives' own sounds) was liked.

## 6. Scene recipes

Working code for the rows that name a scene is in `examples/sample-talk/scenes/Recipes.tsx` (a fictional talk). Build the others from the same primitives.

| Slide type | Recipe | Code |
|---|---|---|
| Title | logos, big title letter by letter, tile motif, venue badge, content warning cued to its phrase | generic `TitleScene` |
| Contribution numbers | 3–4 columns: Counter + label + icon row, column rules drawing down, Stamp for "public release" | `Contribution` |
| Related-work table | rebuilt rows rising one by one, HandCircle on the gap, own row last in the primary colour | `RelatedWork` |
| Pipeline / complex figure | deck image in a card + FocusBox regions in spoken order + HandArrows + Chips + a Counter for the total | `FigureWalkthrough` |
| Main result | HBars with `focus` on the best, HandCircle on its value, a counted delta, riser + chime | `MainResult` |
| Takeaways | numbered cards with Marks, a dark "Next" panel | `Takeaways` |
| Thank you | dark paper page, contact, QR card cropped from the deck | `Thanks` |
| Motivating examples | deck images (example inputs) in cards, labels as Chips cued to their words, HandCircle on the key detail, Note with the takeaway | |
| Taxonomy / definitions | definition card with Marks on the key terms; category Chips in groups (highlight every member of a set, not only the spoken examples); agreement scores as Counters | |
| Distribution | HBars sorted, focus on the head, Note on the long tail | |
| Model list | grouped Chips per model family with icons; setting tags (zero-shot, few-shot, fine-tuned) | |
| Hard task | bars on a lower scale, a dashed line for the ceiling, Note | |
| Ablation | grouped bars (e.g. variant A, B, A+B), deltas as Notes | |
| Error analysis | two "pages" with a camera tilt between them, small multiples | |

## 7. Writing a custom scene

```tsx
// src/scenes/S07.tsx
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {C} from '../theme';
import {HandArrow, Header, Note, Sfx, useAt} from '../lib';
import {HBars} from '../charts';

export const S07: React.FC = () => {
  const at = useAt();
  const tBars = at('we compare');          // first spoken cue
  const tBest = at('best performance');
  const rows = [
    {label: 'Model B, fine-tuned', value: 0.81, color: C.blue},
    {label: 'Model A, zero-shot', value: 0.69, color: C.cyan},
  ]; // values copied from the deck (facts.md: slide 7 chart)
  return (
    <AbsoluteFill>
      <Header kicker="Results" title="Fine-tuning gives the best model" />
      <HBars rows={rows} at={tBars} x={120} y={300} w={1300} labelW={380} min={0.5} max={0.9} dec={2}
             focus={[{at: tBest, keep: [0]}]} />
      <Note at={tBest + 0.4} x={1450} y={330} color={C.bad}>best</Note>
      <HandArrow at={tBest + 0.2} x1={1440} y1={360} x2={1330} y2={330} />
      <Sfx at={tBest - 0.6} name="riser" vol={0.06} />
    </AbsoluteFill>
  );
};
```

Register it in `src/scenes/index.ts`: `import {S07} from './S07'; export const CUSTOM = {7: S07};`. Keys are slide numbers. Scenes must be deterministic: no `Math.random()` or `Date`. Use the `seed` props, or compute from indices.

## 8. Generic scenes

`src/data/slide_cues.json` drives `SlideScene` (slide image + annotations). `x, y, w, h` are fractions of the slide image; `at` and `until` are spoken phrases or seconds:

```json
{"4": [
  {"type": "box",    "at": "12,000",           "x": 0.035, "y": 0.27, "w": 0.235, "h": 0.32},
  {"type": "circle", "at": "eight categories", "x": 0.285, "y": 0.27, "w": 0.095, "h": 0.12},
  {"type": "zoom",   "at": "We benchmark", "until": "We also release", "x": 0.51, "y": 0.25, "w": 0.21, "h": 0.55},
  {"type": "note",   "at": "automatic labels", "x": 0.74, "y": 0.64, "text": "auto-labeled"},
  {"type": "mark",   "at": "publicly",       "x": 0.04, "y": 0.825, "w": 0.385, "h": 0.04}
]}
```

To find coordinates, look at `W/deck/slideNN.png` and estimate fractions; then check with `preview.py --at 4:"12,000"`. Zoom is limited to 2.4×. Annotations zoom with the slide.

`src/data/slide_points.json` drives `PointsScene` (no image). Every `at` is a phrase from that slide:

```json
{"2": {"kicker": "Motivation", "title": "Existing benchmarks are too coarse",
  "points": [{"text": "Most datasets give one label per item", "at": "one label", "icon": "IPost"},
             {"text": "Fine-grained labels show what models miss", "at": "what models miss", "icon": "ITarget", "mark": "what models miss"}],
  "big": {"value": 12000, "label": "labeled questions", "at": "12,000"},
  "stamp": {"text": "Finer labels", "at": "fine-grained"},
  "note": {"text": "not human-verified", "at": "automatic labels"}}}
```

Fallback order per slide: custom scene → TitleScene (first slide, if `authors` is set) → PointsScene (if it has points) → SlideScene (if there's an image) → PointsScene with the section name and first spoken sentence.

## 9. Palette and fonts

- `project.json` `palette`: `primary` (main colour, bars, kickers), `ink` (text, navy), `accent` (marker highlights, rules), `paper` (background), `bad` (red: errors, negative class, circles), `good` (green: verdicts).
  - The default is QCRI-like: #0088C8, #181050, #58C0E8, #F6F4EE, #C0283D, #1E8576.
  - `palette_from_logo.py --logo <file>` samples primary, ink and accent from an institution logo. Check the contrast of `ink` on `paper` afterwards.
- Fonts are bundled (OFL) and embedded as base64: Inter for text, Caveat for handwriting, Cairo for Arabic. For other scripts, add an OFL font to `public/fonts/` and to `make_assets.py` `fonts` and `Root.tsx` `faces`.
- Arabic or other RTL text: wrap it in `<span dir="rtl" style={{fontFamily: F.ar}}>`.

## 10. QA loop

1. `preview.py --work W --slides` renders 3 frames per slide into one sheet. Look at it with your image viewer.
2. Check for:
   - overlapping elements, and text overflowing a card;
   - elements under the caption band;
   - anything still animating at 95 %, or appearing after the speaker moved on;
   - empty-looking frames at 25 % (cue too late);
   - wrong numbers against `facts.md`.
3. Zoom in on single moments with `preview.py --at 6:"error analysis"`.
4. Fix, then preview only the affected slides: `--slides 6 9`.
5. Render only when the sheets are clean. A full render of 6 minutes takes about 15–25 minutes on a laptop.
