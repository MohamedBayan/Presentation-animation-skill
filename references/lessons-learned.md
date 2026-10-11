# Lessons learned (real failures and their fixes)

Each fix below is already built into the scripts or template. This list explains why, so you don't undo the fixes.

## User trust

- **PowerPoint COM closed the user's open deck and lost unsaved edits** (`Quit()` on a running instance). `export_slides.ps1` now opens a copy read-only, without a window, and quits PowerPoint only if it wasn't already running with presentations open. Never call `Quit()` or `Close()` on presentations you didn't open.
- **"Are you sure you edited it? I still hear repeats."** Whole-file Whisper merged the retakes, so the first pass missed eight of them. The island audit (`audit.py`) exists because of this. Run it on raw and on cut audio, and read the files.
- **"The voice is unclear now, very low quality."** Bandwidth extension (SBR) on 16 kHz recordings. Rolled back to the conservative chain, and an A/B folder was given to the user. Don't "improve" audio beyond the chain without an A/B the user approves.
- **Logos:** two partner logos couldn't be found from official sources, and the user noticed they were missing. Say up front which logos you have and which you need, rather than silently leaving them out. Never recreate a logo.
- **Highlighting a subset when the slide lists more** (a definition slide listed eight categories, but only the four the speaker named as examples were highlighted). Highlight everything the speaker or slide treats as the set, not just the examples spoken aloud.

## Remotion

- **Font `delayRender` timeouts in long renders.** Fonts loaded over the network stalled late browser tabs. They're now embedded as base64 in `fontsData.ts`, with `delayRender(..., {retries: 4})`, chunked renders, and no forced `Config.setChromiumOpenGlRenderer('angle')`.
- **Transient CLI `RangeError: Invalid count value: -1`** (a progress-bar bug on narrow terminals). Harmless, but it can abort a render; the chunk retry absorbs it.
- **`<Freeze>` preview showed the wrong frames:** `Freeze` clamps to the composition duration, so `Preview` must have the full timeline duration (already done in `Root.tsx`).
- **Text wrapping inside absolute wrappers of zero width:** give positioned containers a width (`At w=`) or `whiteSpace: 'nowrap'`.
- **Remotion's audio mixer attenuated the mono narration by about 7.7 dB** relative to the SFX. Render the SFX stem alone and mix in Python (`master_mix.py`).
- **Studio A/V desync** (user report): the Studio's mastered track was stale after a timing change. Rebuild it after every timing change (`render.py` stages sfx and master).
- **Phrase cues broke after re-transcription** ("details" became "detail", "5000" became "5" ",000"). `wordAt` now matches across token splits. Still re-preview after every re-cut, and use distinctive phrases with `occ` instead of fixed seconds.
- **Handwritten notes lost their last letters:** the write-on `clipPath` cut glyph overhang. `Note` pads its clip by -8 %/-25 %; keep that if you write your own.
- **Overlapping notes on a dense slide:** check the `preview.py` sheet at 95 % of each slide, when everything is on screen.

## Captions and text

- **ASR errors in captions:** a technical term misheard as a similar-sounding phrase, "on" heard instead of "and" between two model names, a dropped plural. Read the SRT once against the deck and put fixes in `corrections.json` (text only, never audio).
- **Captions:** small (26 px), one line, at most 50 characters, a pill at the bottom centre, with the current word tinted. Big two-line captions covered the content.

## Pipeline and environment

- **Several Pythons on one machine:** only one had faster-whisper. `check_env.py` finds it; use it for every script.
- **Windows console cp1252 crashed on printed non-ASCII transcripts.** `common.py` forces UTF-8 stdout.
- **`/tmp` paths differ between Git Bash and Windows Python.** Use absolute Windows paths, or the session's scratchpad.
- **Bash heredocs with nested quotes broke patch scripts.** Write the script to a file with the editor tool, then run it.
- **`build_timeline.py` before `make_assets.py` created `remotion/src/data` first**, and the template copy was skipped. `make_assets.py` now checks for `package.json` and never overwrites generated data or your scenes.
- **Full-range video:** Remotion's H.264 is `yuvj420p` (full-range BT.601) and plays washed out or crushed in some players. `mux.py` converts to limited-range BT.709 `yuv420p`.
