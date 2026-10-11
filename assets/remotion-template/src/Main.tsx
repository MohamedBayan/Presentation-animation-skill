import React from 'react';
import {AbsoluteFill, Audio, Img, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Captions} from './Captions';
import tl from './data/timeline.json';
import P from './data/project.json';
import {C, F} from './theme';
import {clamp01, EINOUT, SceneCtx} from './lib';
import {sceneFor} from './scenes';

const proj = P as any;
export const TR = 9; // half-length of a transition in frames: 0.6 s total, fits inside the ~0.6 s pause between slides

/** chapters from project.json: [{"from": 3, "name": "Dataset"}, ...]. Empty = no chapter wipes, plain pushes. */
export const SECTIONS: {from: number; name: string}[] = proj.sections ?? [];
export const sectionOf = (n: number) => {
  let k = -1;
  SECTIONS.forEach((s, i) => {
    if (n >= s.from) k = i;
  });
  return k;
};
const isWipe = (i: number) => i > 0 && SECTIONS.length > 0 && sectionOf(tl.slides[i].n) !== sectionOf(tl.slides[i - 1].n);

/** x of the chapter panel's left edge for a wipe centred on global frame b */
export const panelX = (f: number, b: number) => {
  if (f < b - TR) return 1920;
  if (f < b - 4) return 1920 * (1 - EINOUT(clamp01((f - (b - TR)) / (TR - 4))));
  if (f <= b + 4) return 0;
  if (f < b + TR) return -1920 * EINOUT(clamp01((f - (b + 4)) / (TR - 4)));
  return -1920;
};

const Shell: React.FC<{i: number; lead: number; muteSfx: boolean}> = ({i, lead, muteSfx}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = tl.slides[i];
  const last = tl.slides.length - 1;
  const g = f + s.startFrame - lead;
  const t = (f - lead) / fps;
  let tx = 0;
  let blur = 0;
  let clip = '';
  if (i > 0) {
    if (isWipe(i)) {
      clip = `inset(0 0 0 ${Math.max(0, Math.min(1920, panelX(g, s.startFrame) + 1920))}px)`;
    } else {
      const p = EINOUT(clamp01(f / (2 * TR)));
      tx += (1 - p) * 1920;
      blur += Math.sin(Math.PI * p) * 5;
    }
  }
  if (i < last) {
    const b = tl.slides[i + 1].startFrame;
    if (isWipe(i + 1)) {
      if (g >= b - TR) clip = `inset(0 ${1920 - Math.max(0, Math.min(1920, panelX(g, b)))}px 0 0)`;
    } else {
      const p = EINOUT(clamp01((g - (b - TR)) / (2 * TR)));
      tx -= p * 1920;
      blur += Math.sin(Math.PI * p) * 5;
    }
  }
  const Comp = sceneFor(s.n, i);
  const drift = 1 + 0.018 * clamp01(t / s.dur);
  return (
    <SceneCtx.Provider value={{t, dur: s.dur, n: s.n, words: s.words, lead, mute: muteSfx}}>
      <AbsoluteFill style={{transform: `translateX(${tx}px)`, filter: blur > 0.2 ? `blur(${blur.toFixed(2)}px)` : undefined, clipPath: clip || undefined}}>
        <AbsoluteFill style={{transform: `scale(${drift})`, transformOrigin: '50% 55%'}}>
          <Comp />
        </AbsoluteFill>
      </AbsoluteFill>
    </SceneCtx.Provider>
  );
};

const ChapterPanel: React.FC<{b: number; idx: number}> = ({b, idx}) => {
  const f = useCurrentFrame();
  const x = panelX(f, b);
  if (x >= 1920 || x <= -1920) return null;
  return (
    <div style={{position: 'absolute', left: x, top: 0, width: 1920, height: 1080, overflow: 'hidden', boxShadow: '0 0 60px rgba(0,0,0,0.35)'}}>
      <Img src={staticFile('img/paper_dark.png')} style={{position: 'absolute', inset: 0, width: 1920, height: 1080}} />
      <div style={{position: 'absolute', left: 0, top: 0, width: 16, height: 1080, background: C.cyan}} />
      <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 40}}>
        <div style={{fontFamily: F.sans, fontWeight: 900, fontSize: 150, color: C.cyan, letterSpacing: -4}}>{String(idx + 1).padStart(2, '0')}</div>
        <div style={{width: 6, height: 150, background: C.blue}} />
        <div style={{fontFamily: F.sans, fontWeight: 800, fontSize: 110, color: C.white, letterSpacing: -2}}>{SECTIONS[idx].name}</div>
      </div>
    </div>
  );
};

/** running header (short title | venue, section) + progress bar; hidden on the first and last slide */
const Chrome: React.FC = () => {
  const f = useCurrentFrame();
  const total = tl.totalFrames;
  if (tl.slides.length < 3) return null;
  let cur = 0;
  tl.slides.forEach((s, i) => {
    if (f >= s.startFrame) cur = i;
  });
  const on = clamp01((f - (tl.slides[1].startFrame - 6)) / 14) * (1 - clamp01((f - (tl.slides[tl.slides.length - 1].startFrame - 6)) / 14));
  if (on <= 0) return null;
  const secIdx = sectionOf(tl.slides[cur].n);
  const lastN = tl.slides[tl.slides.length - 1].n;
  return (
    <AbsoluteFill style={{opacity: on, pointerEvents: 'none'}}>
      <div style={{position: 'absolute', left: 120, top: 38, display: 'flex', alignItems: 'center', gap: 14, fontFamily: F.sans, fontSize: 20, color: C.grayDark}}>
        <div style={{width: 14, height: 14, background: C.blue, transform: 'rotate(45deg)'}} />
        <span style={{fontWeight: 800, color: C.ink, letterSpacing: 1}}>{proj.short_title ?? ''}</span>
        {proj.venue ? (
          <>
            <span style={{color: C.gray}}>|</span>
            <span>{proj.venue}</span>
          </>
        ) : null}
      </div>
      {secIdx >= 0 ? (
        <div style={{position: 'absolute', right: 120, top: 38, fontFamily: F.sans, fontSize: 20, color: C.grayDark, letterSpacing: 2, textTransform: 'uppercase'}}>
          <span style={{color: C.blue, fontWeight: 800}}>{String(secIdx + 1).padStart(2, '0')}</span>&nbsp;&nbsp;{SECTIONS[secIdx].name}
        </div>
      ) : null}
      <div style={{position: 'absolute', left: 120, right: 120, top: 1040, height: 4, background: C.line, borderRadius: 2}}>
        <div style={{position: 'absolute', left: 0, top: 0, height: 4, width: `${(f / total) * 100}%`, background: C.blue, borderRadius: 2}} />
        {SECTIONS.slice(1).map((s) => {
          const sl = tl.slides.find((x) => x.n === s.from);
          return sl ? <div key={s.name} style={{position: 'absolute', left: `${(sl.startFrame / total) * 100}%`, top: -4, width: 3, height: 12, background: C.ink, opacity: 0.5}} /> : null;
        })}
      </div>
      <div style={{position: 'absolute', right: 120, top: 1008, fontFamily: F.sans, fontSize: 18, color: C.grayDark, fontVariantNumeric: 'tabular-nums'}}>
        {String(tl.slides[cur].n).padStart(2, '0')} / {lastN}
      </div>
    </AbsoluteFill>
  );
};

export type MainProps = {
  /** burn the small word-synced captions into the picture */
  captions?: boolean;
  /** 'mastered' = the final mastered mix (public/audio/final_mix_master.wav) as one track: use for final renders from the Studio.
   *  'live' = narration clips + SFX mixed by Remotion (follows SFX edits live; not loudness-mastered).
   *  'sfxOnly' = SFX stem only (scripts/master_mix.py mixes it with the narration). */
  audio?: 'mastered' | 'live' | 'sfxOnly';
};

export const Main: React.FC<MainProps> = ({captions = false, audio = 'live'}) => {
  const SFX_ONLY = audio === 'sfxOnly';
  const MASTERED = audio === 'mastered';
  const slides = tl.slides;
  const last = slides.length - 1;
  return (
    <AbsoluteFill style={{background: C.paper}}>
      <Img src={staticFile('img/paper.png')} style={{position: 'absolute', inset: 0, width: 1920, height: 1080}} />
      {slides.map((s, i) => {
        const lead = i === 0 ? 0 : TR;
        const tail = i === last ? 0 : TR;
        return (
          <Sequence key={'v' + i} from={s.startFrame - lead} durationInFrames={s.frames + lead + tail} layout="none">
            <Shell i={i} lead={lead} muteSfx={MASTERED} />
          </Sequence>
        );
      })}
      <Chrome />
      {captions ? <Captions /> : null}
      {slides.map((s, i) =>
        isWipe(i) ? (
          <Sequence key={'w' + i} from={0} layout="none">
            <ChapterPanel b={s.startFrame} idx={sectionOf(s.n)} />
          </Sequence>
        ) : null,
      )}
      {SFX_ONLY || MASTERED
        ? null
        : slides.map((s, i) => (
            <Sequence key={'a' + i} from={s.startFrame} durationInFrames={s.frames} layout="none">
              <Audio src={staticFile(`audio/rec${String(s.n).padStart(2, '0')}.wav`)} />
            </Sequence>
          ))}
      {MASTERED ? <Audio src={staticFile('audio/final_mix_master.wav')} /> : null}
      {MASTERED
        ? null
        : slides.map((s, i) =>
            i > 0 ? (
              <Sequence key={'t' + i} from={s.startFrame - (isWipe(i) ? TR : 10)} durationInFrames={60} layout="none">
                <Audio src={staticFile(isWipe(i) ? 'sfx/whoosh_soft.wav' : 'sfx/whoosh.wav')} volume={isWipe(i) ? 0.16 : 0.1} />
              </Sequence>
            ) : null,
          )}
    </AbsoluteFill>
  );
};
