# Narration editing

Goal: the speaker sounds fluent and natural, and every word they meant to say is still there, unchanged.

## What to cut

| Kind | Example | Keep |
|---|---|---|
| Retake / restart | "We benchmark five models. ... We benchmark five model families under..." | the complete, later take |
| False start | "Understanding the context and ... Understanding the context and the domain is essential." | the full sentence |
| Self-correction | "We used micro F1 ... macro-F1 as the main metric" | the corrected version |
| Repeated word / echo | "The model sometimes understood. Understood the wording" | one occurrence, chosen so the sentence reads right |
| Dead air | a 4 s gap mid-sentence while the speaker looked at notes | shortened to the context cap (automatic) |
| Isolated filler | an "uh" or "um" standing alone between pauses | cut it if it is its own island; leave fillers inside fluent speech alone |
| Off-talk | "wait, let me start again", coughs, sighs on their own | cut |

Don't cut:

- hesitations that sound natural;
- emphasis repeats the speaker meant ("very, very important");
- breaths at sentence starts (the -50 dBFS silence threshold keeps them);
- anything where the remaining audio would need a word that wasn't said. Flag it instead and suggest the user re-record that sentence.

When a retake differs in content (different numbers, different claim), keep the take that matches the deck. If neither matches, keep the later one and flag it.

## Finding the problems

1. `transcribe.py --stage raw` produces whole-file transcripts in `W/transcripts/raw/recNN.txt`, with segment times.
2. `audit.py --stage raw` splits each recording at pauses (90 ms median level below -40 dBFS for at least 0.25 s) and transcribes every island on its own. Whole-file Whisper hides retakes because it "cleans up" repeated phrases into one; island transcription doesn't. The script prints suspects:
   - `REPEAT`: an island starts with the same 2+ words as the previous one.
   - `ECHO`: the last word of an island equals the first word of the next.
   - `FRAGMENT`: an island of fewer than 4 words followed by a pause, often an abandoned start.
3. **Read the full audit file of every recording anyway.** The automatic suspects miss restarts that use different words, and many FRAGMENTs are fine (a short phrase before a comma pause).
4. Compare against the slide text and notes. A sentence that appears twice with a small change is a retake.

## Writing `W/edit_plan.json`

```json
{
 "defaults": {"lead_in": 0.25, "tail": 0.35, "speech_thr": -32, "gap_thr": -50,
              "gap_sentence": 0.42, "gap_comma": 0.28, "gap_word": 0.18, "snap": 0.10, "xfade": 0.012},
 "recordings": {
  "rec04": {"remove": [
    {"start": 5.7, "end": 8.6, "reason": "FALSE START: 'We collected 12000 que-' (5.8-7.9) removed; restart 'We collected 12,000 questions from ...' (8.7-) kept"},
    {"start": 21.2, "end": 24.9, "reason": "RETAKE: 'We benchmark five models.' removed; 'We benchmark five model families ...' kept"}
  ]}
 }
}
```

- Times are in **original recording seconds** (the raw transcript and audit times).
- Put both edges inside silence: from the end of the last kept word to just before the first word you remove, and from the end of the removed take to just before the kept take. Edges snap to the quietest 10 ms within ±`snap`.
- Start every reason with a tag (`RETAKE`, `FALSE START`, `SELF-CORRECTION`, `REPEAT`, `DEAD AIR`, `FILLER`, `OFF-TALK`). Quote what was removed and what was kept. `report.py` copies these reasons into the user's report.
- A cut inside continuous speech (no pause between the takes) is allowed only at a verified dip:
  1. Run `probe.py energy recNN t0 t1 --ms 10` and pick the deepest point between the two words, ideally below -35 dBFS.
  2. Run `probe.py join recNN a-b c-d` to transcribe the joined result.
  3. Add `FLAG` to the reason, so the spot lands in the report's "please listen" list.
- Defaults rarely need changing. A very fast speaker may want `gap_word` 0.22; a slow and deliberate one may want `gap_sentence` 0.5. Tight pacing (0.42/0.28/0.18) is what a user asked for ("remove silent moments, make it flowy").

## Applying and re-checking

- `cut.py` writes `cut/recNN.wav`, `recNN_map.json` (original→new time map) and `cut_log.md`. Check every join's loudest 10 ms frame. Below -50 dBFS is a clean join; above that, look at the cut.
- `enhance.py`, then `transcribe.py --stage cut` and `audit.py --stage cut`. The cut-stage audit must be clean: no REPEAT or ECHO left, and every FRAGMENT explained.
- Compare raw and cut word counts per recording (`transcripts/raw` vs `transcripts/cut`). The difference must be exactly the words you meant to remove. A lost word in between means a pause cap ate a quiet word; lower `gap_thr` for that recording to -55 and re-cut.
- Iterate with `--only rec04 rec07` on `transcribe.py`, `audit.py` and `cut.py` to touch only what changed. After any re-cut, steps 6–9 must run again: timeline, assets and render. `render.py --fresh` handles the render side.
