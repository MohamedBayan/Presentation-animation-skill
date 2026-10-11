# Audio

## The chain (`enhance.py`, per clip, after cutting)

1. Resample to 48 kHz with soxr (`aresample=resampler=soxr:precision=28`): video-standard rate, no aliasing.
2. High-pass at 80 Hz: removes handling noise and rumble below the voice.
3. -2 dB peaking EQ at 300 Hz (`--mud`): phone mics close to the mouth are boomy; this removes boxiness.
4. +2 dB at 2.6 kHz (`--presence`): intelligibility band for consonants. Don't push it beyond +3 dB, or "s" and "t" turn harsh.
5. Compressor at 2:1 above -22 dBFS (12 ms attack, 180 ms release, soft 6 dB knee): evens out loud and soft phrases, staying gentle.
6. Static gain to -16 LUFS integrated, then the limiter (`alimiter`, ceiling -2 dBFS) runs at 192 kHz, so inter-sample peaks are caught. True peak lands near -2 dBTP, the clip near -16.5 LUFS, and the limiter touches about 0.1 % of samples.
7. Output: `clean/recNN.wav`, 48 kHz, 24-bit, mono. `loudness_stats.json` records LUFS, true peak, LRA and the limiter percentage per clip.

After mixing the SFX, `master_mix.py` brings the whole program to -16 LUFS with true peak at or below -1 dBTP, the common target for conference uploads and YouTube. Platforms that want -23 LUFS (EBU R128 broadcast) are rare for talks; use `--target -23` on both `enhance.py` and `master_mix.py` if one asks.

## What was tried and rejected (don't repeat it)

- **SBR-style bandwidth extension** (rebuilding 8–16 kHz from the 4–8 kHz band) on 16 kHz iPhone recordings: the user heard the voice as "unclear, very low quality". It added a metallic, phasey sheen.
- **AI super-resolution** (ClearerVoice MossFormer2_SR_48K): on this material it produced only tonal artifacts above 8 kHz.
- **Heavy denoising** (RNNoise or strong `afftdn`): makes the voice watery. Recordings in a quiet room don't need it.

The conservative chain was what the user accepted. If a recording is genuinely noisy (fan, traffic), offer an A/B before switching:

```bash
ffmpeg -i clean/rec03.wav -af "afftdn=nr=8:nf=-45:tn=1" out/ab/rec03_denoise.wav
```

Give the user 20 s of each version (`W/out/ab/`) and let them choose. Never decide that a processed version "sounds better" without the user's ears.

## Low-bandwidth sources

A 16 kHz AAC recording has nothing above 8 kHz, and no processing brings it back honestly. Say so plainly. The voice will sound like a good phone call, which is fine for a talk. For future recordings, suggest lossless Voice Memos, a quiet room with soft furnishings, and the phone 20 cm away, slightly off-axis.

## Music

None by default: talks with background music are harder to follow, and conferences rarely want it. If the user asks for intro or outro music, it must be royalty-free and named in the report. Duck it at least 20 dB under the voice, and only under the title and end cards.
