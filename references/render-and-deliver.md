# Render, verify, deliver

## Render (`render.py`)

```bash
$PY $S/render.py --work W --fresh                 # everything
$PY $S/render.py --work W --stages master,mux,verify   # audio-only change (SFX volumes), picture unchanged
```

| Stage | What | Why it's done this way |
|---|---|---|
| chunks | `Pipeline` composition, muted, H.264 CRF 16, 8 frame-exact chunks, each retried up to 4× | A single long render sometimes dies when Remotion opens a late browser tab; one chunk retries cheaply |
| sfx | `Pipeline` with `{"audio":"sfxOnly"}` → `out/sfx_stem.wav` | Remotion's mixer attenuated the narration by about 7.7 dB against the SFX, so the voice is mixed outside |
| caps | `CaptionsOnly` → transparent PNGs `out/caps/cap_%05d.png` | One picture render serves both the captioned and the clean MP4 |
| master | narration placed at each slide's start frame + SFX stem (peak -17.5 dBFS) → -16 LUFS, true peak ≤ -1 dBTP | Also copies the mix to `remotion/public/audio/final_mix_master.wav` for the Studio |
| mux | RGB overlay of the caption PNGs, BT.601 full range → BT.709 limited `yuv420p`, x264 CRF 16 `-tune animation`, AAC 192k, `+faststart` | Players show Remotion's raw full-range output washed out; this conversion avoids it |
| verify | format, frame count = timeline, loudness, black frames, silences over 1 s, clipping, Whisper re-transcription of anchor words (A/V sync), contact sheet | Writes `out/verify_<file>.json` for `report.py` |

**Always pass `--fresh` after changing scenes, cues or timing.** Without it, existing chunks are reused, which is right only when resuming a crashed render.

A 6-minute talk takes about 15–25 minutes for the chunks, plus about 3 minutes for captions, on a laptop with `--concurrency 4`. Run it in the background and do the report meanwhile.

The plain slides version, if wanted: `$PY $S/slides_video.py --work W`. It uses `<name>_slides_version.srt` from `build_timeline.py --static`.

## Verify, honestly

- Look at `out/verify_sheet_<file>.jpg`: one frame at 62 % of every scene.
- Sync: the median should be within ±40 ms and the worst within about 150 ms. Larger errors mean the timeline and the audio disagree; usually a stale `clean/` or `timeline.json`, so re-run steps 6–9.
- Silences over 1 s: only the end hold should appear (`--hold`, 1.5 s by default).
- Report the results as automated measurements. Don't write "I listened" or "sounds great".

## Report and hand-off

1. `$PY $S/report.py --work W` drafts `delivery/EDIT_REPORT.md` with:
   - the deliverables table;
   - every cut with its time in the final video;
   - per-slide durations and the "please listen" list;
   - the audio chain and loudness, QA results, and caption fixes.
2. Edit the draft by hand. Add what the user specifically asked for and how you did it, plus open items (a missing logo, a sentence they might re-record).
3. Copy `W/facts.md` to `delivery/facts_on_screen.md` and the clean WAVs to `delivery/cleaned_recordings_wav/` (names like `slide04_<original name>_clean.wav`).
4. Message the user (short):
   - the paths of the main MP4 and the clean version;
   - running time, loudness, and the A/V sync result;
   - 3–8 timestamps to listen to, from the report;
   - how to tweak: open a terminal in `W/remotion` and run `npx remotion studio`. "Talk-final" plays the mastered mix with captions; the props panel toggles captions. Render from the Studio UI, or ask you to change things.
   - what's still open.

## Studio (the user's timeline UI)

- `npx remotion studio` in `W/remotion` opens http://localhost:3000. In the Claude desktop app, add a `.claude/launch.json` entry (`npx remotion studio --port 3123 --no-open`) and open it in the preview pane for the user.
- Compositions:
  - `Talk-final`: mastered audio, with captions.
  - `Talk-clean`: mastered audio, without captions.
  - `Pipeline`: live mix of narration and SFX, which follows SFX edits.
  - `CaptionsOnly` and `Preview`: used by the scripts.
- **Sync rule:** `Talk-final` plays `public/audio/final_mix_master.wav`. After any timing change (re-cut, `--hold`, scene durations), run `render.py --stages sfx,master` at least, or the Studio picture runs out of sync with that stale track. That is the exact bug a user reported.

## Change requests → what to re-run

| User asks | Edit | Re-run |
|---|---|---|
| "Still hear a repeat at 1:23" | Find the slide from the report table and the time in `transcripts/cut`, then add a remove (original seconds; map via `cut/recNN_map.json`) | `cut --only`, `enhance`, `transcribe --stage cut --only`, `audit --stage cut --only`, `build_timeline`, `make_assets`, `preview`, `render --fresh`, `report` |
| "Less / more pause" | `edit_plan.json` defaults (`gap_*`) | same as above for all recordings |
| "Voice sounds thin / boomy / harsh" | `enhance.py --presence/--mud`; offer an A/B of 20 s first | `enhance`, `make_assets`, `render --stages sfx,master,mux,verify` |
| "SFX too loud / more SFX" | `master_mix.py --sfx-peak -20` / add `<Sfx>` or primitives | louder or softer only: `render --stages master,mux,verify`; new SFX: `--stages sfx,master,mux,verify` |
| "Highlight X on slide 6" | scene or cue JSON | `preview --slides 6`, `render --fresh` |
| Wrong word in captions | `corrections.json` | `build_timeline`, `render --stages caps,mux,verify --fresh` (`--fresh` also clears the old caption PNGs; add `chunks` only if scenes changed) |
| New logo | file → `project.json` logos | `make_assets`, `preview --slides 1`, `render --fresh` |
| Different colours | `project.json` palette | `build_timeline` (copies project.json), `make_assets` (paper textures), `render --fresh` |

Note: `--fresh` clears both the picture chunks and the caption PNGs for the stages you list.
