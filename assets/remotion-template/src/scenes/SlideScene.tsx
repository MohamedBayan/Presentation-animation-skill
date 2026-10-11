import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import cuesData from '../data/slide_cues.json';
import {C} from '../theme';
import {EINOUT, FocusBox, HandCircle, Note, prog, Rise, Sfx, useScene, wordAt, lerp, Word} from '../lib';

/**
 * Generic scene: the rendered slide image (public/slides/slideNN.png) on paper, animated by cues timed to speech.
 * src/data/slide_cues.json:
 * {
 *   "4": [
 *     {"type": "zoom",   "at": "three model families", "until": "we also release", "x": 0.50, "y": 0.25, "w": 0.24, "h": 0.55},
 *     {"type": "box",    "at": "12,000", "x": 0.04, "y": 0.28, "w": 0.22, "h": 0.30},
 *     {"type": "circle", "at": "eight categories", "x": 0.30, "y": 0.28, "w": 0.10, "h": 0.12},
 *     {"type": "mark",   "at": "publicly", "x": 0.04, "y": 0.83, "w": 0.40, "h": 0.04},
 *     {"type": "note",   "at": "automatic labels", "x": 0.75, "y": 0.70, "text": "not human-verified"}
 *   ]
 * }
 * x, y, w, h are FRACTIONS of the slide image. "at"/"until" are a spoken phrase (matched in this slide's transcript,
 * add "occ": 1 for the 2nd occurrence) or seconds from the slide's start. Annotations zoom with the slide.
 */
type Cue = {type: 'zoom' | 'box' | 'circle' | 'mark' | 'note'; at: string | number; until?: string | number; occ?: number;
  x: number; y: number; w?: number; h?: number; text?: string; color?: string};

const BOX = {x: 200, y: 92, w: 1520, h: 855};

const resolve = (words: Word[], v: string | number | undefined, occ = 0, fallback = 0) => {
  if (v === undefined) return fallback;
  if (typeof v === 'number') return v;
  try {
    return wordAt(words, v, occ);
  } catch {
    return fallback; // phrase not spoken: show at the fallback time instead of failing the render
  }
};

export const SlideScene: React.FC = () => {
  const {t, n, words, dur} = useScene();
  const cues: Cue[] = ((cuesData as any)[String(n)] ?? []) as Cue[];
  const timed = cues.map((c) => ({...c, t0: resolve(words, c.at, c.occ ?? 0, 0.5)}));
  // camera: sequential zooms
  let z = 1;
  let cx = 0.5;
  let cy = 0.5;
  for (const c of timed.filter((c) => c.type === 'zoom')) {
    const t1 = resolve(words, c.until, 0, c.t0 + 3.5);
    const p = prog(t, c.t0 - 0.2, 0.7, EINOUT) * (1 - prog(t, t1, 0.7, EINOUT));
    if (p > 0) {
      const zz = Math.min(2.4, 0.9 / (c.w ?? 0.4), 0.9 / (c.h ?? 0.4));
      z = lerp(1, zz, p);
      cx = lerp(0.5, c.x + (c.w ?? 0) / 2, p);
      cy = lerp(0.5, c.y + (c.h ?? 0) / 2, p);
    }
  }
  const tx = (0.5 - cx) * BOX.w * z;
  const ty = (0.5 - cy) * BOX.h * z;
  const px = (fx: number) => fx * BOX.w;
  const py = (fy: number) => fy * BOX.h;
  return (
    <AbsoluteFill>
      <Rise at={0.05} from={0.97} style={{position: 'absolute', left: BOX.x, top: BOX.y, width: BOX.w, height: BOX.h}}>
        <div style={{position: 'absolute', inset: -12, background: C.white, borderRadius: 10, boxShadow: '0 16px 40px rgba(24,16,80,0.16), 0 2px 6px rgba(24,16,80,0.08)'}} />
        <div style={{position: 'absolute', inset: 0, overflow: 'hidden', borderRadius: 4}}>
          <div style={{position: 'absolute', inset: 0, transform: `translate(${tx}px, ${ty}px) scale(${z})`, transformOrigin: '50% 50%'}}>
            <Img src={staticFile(`slides/slide${String(n).padStart(2, '0')}.png`)} style={{width: BOX.w, height: BOX.h, display: 'block'}} />
            {timed.map((c, i) => {
              const col = c.color ?? (c.type === 'circle' ? C.bad : C.blue);
              if (c.type === 'box')
                return <FocusBox key={i} at={c.t0} x={px(c.x)} y={py(c.y)} w={px(c.w ?? 0.1)} h={py(c.h ?? 0.1)} color={col} sw={4} />;
              if (c.type === 'circle')
                return <HandCircle key={i} at={c.t0} x={px(c.x)} y={py(c.y)} w={px(c.w ?? 0.1)} h={py(c.h ?? 0.1)} color={col} sw={5} seed={i + 1} />;
              if (c.type === 'mark') {
                const p = prog(t, c.t0, 0.45, EINOUT);
                return (
                  <React.Fragment key={i}>
                    <Sfx at={c.t0} name="marker" vol={0.04} />
                    <div style={{position: 'absolute', left: px(c.x), top: py(c.y), width: px(c.w ?? 0.2) * p, height: py(c.h ?? 0.04),
                      background: c.color ?? C.cyan, opacity: 0.35, mixBlendMode: 'multiply', borderRadius: 3}} />
                  </React.Fragment>
                );
              }
              if (c.type === 'note')
                return (
                  <Note key={i} at={c.t0} x={px(c.x)} y={py(c.y)} size={42} color={c.color ?? C.blue} rot={-3}>
                    {c.text ?? ''}
                  </Note>
                );
              return null;
            })}
          </div>
        </div>
      </Rise>
      {timed.filter((c) => c.type === 'zoom').map((c, i) => (
        <Sfx key={'z' + i} at={c.t0 - 0.2} name="swish" vol={0.05} />
      ))}
    </AbsoluteFill>
  );
};
