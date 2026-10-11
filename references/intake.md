# Intake: what the user gives you and how to map it

`ingest.py` accepts:

- **Recordings**: a zip, a folder or a list of files.
  - Audio: m4a, wav, mp3, aac, flac, ogg, opus.
  - Video (mp4, mov, mkv, webm): the audio is extracted. If it's a screen recording with the slides visible, ask whether they want the animated version or just a cleaned-up version of their own video.
- **Deck** (optional):
  - pptx: rendered through PowerPoint COM on a copy, or LibreOffice when PowerPoint isn't installed.
  - pdf: rendered with PyMuPDF.
  - Keynote or Google Slides: ask for a PDF or PPTX export.

It writes:

- `mapping.json`: slide number → recording.
- `raw/recNN.wav`: 16 kHz mono. NN is the slide number, so `rec04` is always slide 4.
- `deck/slides.json`: per-slide text, speaker notes, hidden flag, animations and media.
- `deck/slideNN.png` and a `project.json` skeleton.

## Mapping recordings to slides

The default is one recording per slide, in order, starting at slide `--first-slide` (1 unless the title slide wasn't recorded).

- **Ordering.** `ingest.py` orders by the recordings' creation time when every file has one; otherwise it uses natural filename order, with an unnumbered file ("Recording.m4a" before "Recording 2.m4a") first. It prints both orders. If they disagree, read the transcripts against the slide text before trusting either.
- **Check the mapping** by comparing each raw transcript's first sentence with the slide text and speaker notes in `deck/slides.json`. The mapping is wrong if, say, the recording for slide 5 talks about slide 6's content. Fix `mapping.json` by hand and re-run ingest with `--recordings` in the right order.
- **Fewer recordings than slides.** Usually appendix or backup slides at the end; they're left out. If a gap is in the middle (a slide without narration), ask: drop the slide, or show it silently for about 3 s?
- **More recordings than slides.** Usually two takes of the same slide. Pick the take with fewer mistakes (normally the later one), say which, and keep the other in `input/` untouched.
- **Hidden slides** with a recording: include them, since the speaker clearly meant to talk over them.

## One long recording (whole talk in one take)

1. Run `ingest.py` as usual. It prints that there's one recording for many slides. Then `transcribe.py --stage raw`.
2. Find the slide boundaries. Look for:
   - phrases that match the next slide's text or notes;
   - transition words ("next", "now let's look at", "moving on");
   - pauses over 0.8 s near those spots (`probe.py energy rec01 <t0> <t1>` shows the level).
3. Write `W/split_plan.json` as `[{"slide": 1, "start": 0, "end": 41.3}, {"slide": 2, "start": 41.3, "end": 88.0}, ...]` in raw seconds.
4. `$PY $S/split.py --work W --source rec01 --plan W/split_plan.json`. Boundaries snap to the quietest 10 ms within ±0.3 s; you get `raw/recNN.wav` per slide, and `mapping.json` is rewritten.
5. Run `transcribe.py --stage raw` again: the pieces need their own transcripts. Then continue at the audit step.

If the speaker went back to an earlier slide, give that stretch its own "slide" entry with the earlier slide number's image. Duplicate the PNG as a new slide number and note it in the report.

## No deck

- Slides are numbered by recording order. `project.json` gets its title from the user or the transcript, so ask for the title, authors and venue in your first message.
- Scenes: write `src/data/slide_points.json` from the transcript (kicker, title, 2–4 points, a big number if one is spoken; see `references/animation-design.md`), or build custom scenes. `SlideScene` is unavailable without slide images.
- One long take and no deck: split by topic into 20–60 s "slides" (step 3 above) so every scene has a focus.
- Skip `slides_video.py`; it needs slide images.

## Slides with builds or embedded media

`ingest.py` flags slides with animations or media (`!! slides with animations or embedded media`).

- **Builds**: the rendered PNG shows the final state of the slide. To reveal parts in sync with speech, cover them with cues in the fast tier, or rebuild the slide as a custom scene.
- **Embedded video or GIF**: a pptx is a zip, so unzip the copy in `W/deck/` into a scratch folder and take the file from `ppt/media/`. `deck/slides.json` names it under `media`. Put it in `remotion/public/media/` and play it with Remotion's `<OffthreadVideo>` inside a custom scene. Tell the user that the plain slides version shows only the poster frame.

## Low sample-rate recordings

iPhone Voice Memos often record AAC at 16–24 kHz, so nothing exists above 8–12 kHz. `ingest.py` warns about anything under 32 kHz. Don't try to invent the missing band (see `references/audio.md`). For next time, suggest Voice Memos → Settings → Audio Quality → Lossless, a quiet small room, and the phone about 20 cm from the mouth, slightly off-axis.
