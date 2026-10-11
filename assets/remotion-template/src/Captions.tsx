import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import caps from './data/captions.json';
import {C, F} from './theme';
import {clamp01} from './lib';

type Line = {start: number; end: number; text: string; words: {w: string; s: number; e: number}[]};
const LINES = caps as Line[];

/** small word-synced caption: one line in a frosted pill above the progress bar; the word being spoken turns QCRI blue */
export const Captions: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = f / fps;
  let k = -1;
  for (let i = 0; i < LINES.length; i++) if (LINES[i].start <= t && t <= LINES[i].end) k = i;
  if (k < 0) return null;
  const L = LINES[k];
  const joinedPrev = k > 0 && L.start - LINES[k - 1].end < 0.25;
  const joinedNext = k + 1 < LINES.length && LINES[k + 1].start - L.end < 0.25;
  const pin = joinedPrev ? 1 : clamp01((t - Math.max(0, L.start)) / 0.15);
  const pout = joinedNext ? 1 : clamp01((L.end - t) / 0.15);
  const o = Math.min(pin, pout);
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: 970, display: 'flex', justifyContent: 'center', pointerEvents: 'none'}}>
      <div style={{opacity: o, transform: `translateY(${(1 - pin) * 6}px)`, background: 'rgba(255,255,255,0.94)', border: '1px solid rgba(24,16,80,0.10)',
        borderRadius: 12, padding: '7px 22px 8px', boxShadow: '0 6px 22px rgba(24,16,80,0.16)', fontFamily: F.sans, fontWeight: 600, fontSize: 26,
        lineHeight: 1.2, color: C.ink, whiteSpace: 'nowrap', letterSpacing: 0.1}}>
        {L.words.map((w, i) => {
          const active = t >= w.s - 0.02 && t < w.e + 0.04;
          return (
            <span key={i} style={{color: active ? C.blue : C.ink}}>
              {w.w}
              {i < L.words.length - 1 ? ' ' : ''}
            </span>
          );
        })}
      </div>
    </div>
  );
};
