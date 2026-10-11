import React, {createContext, useContext} from 'react';
import {Audio, Easing, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, F} from './theme';

// ---------------------------------------------------------------- scene context
export type Word = {w: string; s: number; e: number};
export type SceneInfo = {t: number; dur: number; n: number; words: Word[]; lead: number; mute?: boolean};
export const SceneCtx = createContext<SceneInfo>({t: 0, dur: 1, n: 1, words: [], lead: 0});
export const useScene = () => useContext(SceneCtx);

const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, '');

/** time (s, relative to the slide's narration start) at which a word / phrase is spoken.
 *  Matching ignores case, punctuation, spaces and how Whisper split the tokens: "12,000" finds "12" ",000",
 *  "state-of-the-art" finds "state" "-of" "-the" "-art". The phrase must start and end on word boundaries. */
export function wordAt(words: Word[], phrase: string, occ = 0, after = 0): number {
  const target = norm(phrase);
  const ws = words.map((w) => ({...w, k: norm(w.w)})).filter((w) => w.k.length > 0);
  let seen = 0;
  for (let i = 0; target && i < ws.length; i++) {
    if (ws[i].s < after || !target.startsWith(ws[i].k)) continue;
    let acc = '';
    for (let j = i; j < ws.length && acc.length < target.length; j++) acc += ws[j].k;
    if (acc === target) {
      if (seen === occ) return ws[i].s;
      seen++;
    }
  }
  throw new Error(`phrase not found: "${phrase}" (occ ${occ})`);
}
export const useAt = () => {
  const {words} = useScene();
  return (phrase: string, occ = 0, after = 0) => wordAt(words, phrase, occ, after);
};

// ---------------------------------------------------------------- easing helpers
export const EOUT = Easing.bezier(0.2, 0.8, 0.2, 1);
export const EINOUT = Easing.bezier(0.65, 0, 0.35, 1);
export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const prog = (t: number, t0: number, d = 0.35, e = EOUT) => e(clamp01((t - t0) / d));
export const lerp = (a: number, b: number, p: number) => a + (b - a) * p;

/** opacity for an element that appears at t0 and (optionally) leaves at t1 */
export const vis = (t: number, t0: number, t1?: number, d = 0.3) => {
  const a = prog(t, t0, d);
  const b = t1 === undefined ? 0 : prog(t, t1, 0.25);
  return a * (1 - b);
};

// ---------------------------------------------------------------- building blocks
type Box = {x?: number; y?: number; w?: number; h?: number};

export const Rise: React.FC<{
  at: number; out?: number; d?: number; dy?: number; dx?: number; from?: number; style?: React.CSSProperties; children?: React.ReactNode;
}> = ({at, out, d = 0.4, dy = 26, dx = 0, from = 0.96, style, children}) => {
  const {t} = useScene();
  const p = prog(t, at, d);
  const o = out === undefined ? 0 : prog(t, out, 0.3);
  return (
    <div style={{...style, opacity: p * (1 - o), transform: `translate(${(1 - p) * dx - o * 30}px, ${(1 - p) * dy}px) scale(${lerp(from, 1, p)})`}}>
      {children}
    </div>
  );
};

/** absolutely positioned container */
export const At: React.FC<Box & {style?: React.CSSProperties; children?: React.ReactNode}> = ({x = 0, y = 0, w, h, style, children}) => (
  <div style={{position: 'absolute', left: x, top: y, width: w, height: h, ...style}}>{children}</div>
);

/** highlighter-marker sweep behind inline text */
const MarkBase: React.FC<{at: number; color?: string; d?: number; children: React.ReactNode; strong?: boolean}> = ({
  at, color = C.cyanSoft, d = 0.45, children, strong,
}) => {
  const {t} = useScene();
  const p = prog(t, at, d, EINOUT);
  return (
    <span
      style={{
        backgroundImage: `linear-gradient(${color}, ${color})`,
        backgroundRepeat: 'no-repeat',
        backgroundPosition: strong ? '0 88%' : '0 80%',
        backgroundSize: `${p * 100}% ${strong ? 92 : 78}%`,
        padding: '0 4px',
        margin: '0 -4px',
        boxDecorationBreak: 'clone',
        WebkitBoxDecorationBreak: 'clone',
      }}
    >
      {children}
    </span>
  );
};

/** small deterministic noise */
const rnd = (i: number) => {
  const x = Math.sin(i * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

/** hand-drawn ellipse that draws itself on (Vox-style annotation); boils slightly "on twos" */
const HandCircleBase: React.FC<{x: number; y: number; w: number; h: number; at: number; color?: string; sw?: number; d?: number; out?: number; seed?: number}> = ({
  x, y, w, h, at, color = C.bad, sw = 5, d = 0.5, out, seed = 1,
}) => {
  const {t} = useScene();
  const frame = useCurrentFrame();
  const p = prog(t, at, d, EINOUT);
  if (p <= 0) return null;
  const boil = Math.floor(frame / 2);
  const pts: [number, number][] = [];
  const N = 60;
  const turns = 1.12;
  for (let i = 0; i <= N; i++) {
    const a = -Math.PI * 0.75 + (i / N) * Math.PI * 2 * turns;
    const r = 1 + (rnd(seed * 31 + i) - 0.5) * 0.05 + (i / N) * 0.06 + (rnd(boil * 7 + i) - 0.5) * 0.012;
    pts.push([w / 2 + (w / 2) * r * Math.cos(a), h / 2 + (h / 2) * r * Math.sin(a)]);
  }
  let len = 0;
  for (let i = 1; i < pts.length; i++) len += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  const dstr = 'M' + pts.map((q) => `${q[0].toFixed(1)} ${q[1].toFixed(1)}`).join(' L');
  const o = out === undefined ? 1 : 1 - prog(t, out, 0.25);
  return (
    <svg style={{position: 'absolute', left: x - 20, top: y - 20, overflow: 'visible', opacity: o}} width={w + 40} height={h + 40}>
      <path d={dstr} transform="translate(20 20)" fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round"
        strokeDasharray={len} strokeDashoffset={len * (1 - p)} />
    </svg>
  );
};

/** hand-drawn curved arrow from (x1,y1) to (x2,y2) */
const HandArrowBase: React.FC<{x1: number; y1: number; x2: number; y2: number; at: number; bend?: number; color?: string; sw?: number; out?: number}> = ({
  x1, y1, x2, y2, at, bend = 0.25, color = C.ink, sw = 4, out,
}) => {
  const {t} = useScene();
  const p = prog(t, at, 0.45, EINOUT);
  if (p <= 0) return null;
  const mx = (x1 + x2) / 2 - (y2 - y1) * bend;
  const my = (y1 + y2) / 2 + (x2 - x1) * bend;
  const d = `M${x1} ${y1} Q${mx} ${my} ${x2} ${y2}`;
  const len = Math.hypot(x2 - x1, y2 - y1) * 1.25;
  const ang = Math.atan2(y2 - my, x2 - mx);
  const head = 18;
  const hp = clamp01((p - 0.8) / 0.2);
  const a1 = ang + Math.PI * 0.82;
  const a2 = ang - Math.PI * 0.82;
  const o = out === undefined ? 1 : 1 - prog(t, out, 0.25);
  return (
    <svg style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', opacity: o}} width={1} height={1}>
      <path d={d} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeDasharray={len} strokeDashoffset={len * (1 - p)} />
      <path d={`M${x2 + Math.cos(a1) * head * hp} ${y2 + Math.sin(a1) * head * hp} L${x2} ${y2} L${x2 + Math.cos(a2) * head * hp} ${y2 + Math.sin(a2) * head * hp}`}
        fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" opacity={hp > 0 ? 1 : 0} />
    </svg>
  );
};

/** handwritten note (Caveat), written on with a left-to-right reveal */
const NoteBase: React.FC<{at: number; x: number; y: number; size?: number; color?: string; rot?: number; children: React.ReactNode; out?: number; w?: number}> = ({
  at, x, y, size = 44, color = C.blue, rot = -3, children, out, w,
}) => {
  const {t} = useScene();
  const p = prog(t, at, 0.55, Easing.linear);
  const o = out === undefined ? 1 : 1 - prog(t, out, 0.25);
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, transform: `rotate(${rot}deg)`, fontFamily: F.hand, fontWeight: 700, fontSize: size,
      color, lineHeight: 1.0, whiteSpace: w ? 'normal' : 'nowrap', clipPath: `inset(-25% ${(1 - p) * 110 - 10}% -25% -8%)`, opacity: o}}>
      {children}
    </div>
  );
};

export const fmt = (v: number, dec = 0, comma = true) => {
  const s = v.toFixed(dec);
  if (!comma) return s;
  const [i, f] = s.split('.');
  return i.replace(/\B(?=(\d{3})+(?!\d))/g, ',') + (f ? '.' + f : '');
};

/** number that counts up from `from` to `to` starting at `at` */
const CounterBase: React.FC<{at: number; to: number; from?: number; d?: number; dec?: number; prefix?: string; suffix?: string; comma?: boolean; style?: React.CSSProperties}> = ({
  at, to, from = 0, d = 0.9, dec = 0, prefix = '', suffix = '', comma = true, style,
}) => {
  const {t} = useScene();
  const p = prog(t, at, d, Easing.bezier(0.1, 0.7, 0.2, 1));
  return (
    <span style={{fontVariantNumeric: 'tabular-nums', ...style}}>
      {prefix}
      {fmt(lerp(from, to, p), dec, comma)}
      {suffix}
    </span>
  );
};

/** rubber stamp label */
const StampBase: React.FC<{at: number; color: string; children: React.ReactNode; rot?: number; size?: number; style?: React.CSSProperties; fill?: string}> = ({
  at, color, children, rot = -4, size = 30, style, fill,
}) => {
  const {t} = useScene();
  const p = prog(t, at, 0.2, Easing.bezier(0.3, 0.9, 0.3, 1));
  if (p <= 0) return null;
  return (
    <div style={{display: 'inline-block', border: `4px solid ${color}`, color, padding: '6px 16px', borderRadius: 8, fontFamily: F.sans, fontWeight: 800, fontSize: size,
      letterSpacing: 1, textTransform: 'uppercase', background: fill ?? 'rgba(255,255,255,0.88)', transform: `rotate(${rot}deg) scale(${lerp(1.35, 1, p)})`, opacity: p, ...style}}>
      {children}
    </div>
  );
};

/** pill chip */
const ChipBase: React.FC<{at: number; color?: string; bg?: string; children: React.ReactNode; size?: number; style?: React.CSSProperties; out?: number; icon?: React.ReactNode}> = ({
  at, color = C.ink, bg = C.white, children, size = 26, style, out, icon,
}) => {
  const {t} = useScene();
  const p = prog(t, at, 0.3);
  const o = out === undefined ? 0 : prog(t, out, 0.25);
  return (
    <div style={{display: 'inline-flex', alignItems: 'center', gap: 10, padding: `${size * 0.32}px ${size * 0.7}px`, borderRadius: 999, background: bg, color,
      border: `2px solid ${color}`, fontFamily: F.sans, fontWeight: 700, fontSize: size, opacity: p * (1 - o), transform: `scale(${lerp(0.9, 1, p)}) translateY(${(1 - p) * 12}px)`,
      boxShadow: '0 4px 12px rgba(24,16,80,0.08)', whiteSpace: 'nowrap', ...style}}>
      {icon}
      {children}
    </div>
  );
};

/** paper card with soft shadow */
export const Card: React.FC<{style?: React.CSSProperties; children?: React.ReactNode; tape?: boolean}> = ({style, children, tape}) => (
  <div style={{position: 'relative', background: C.white, borderRadius: 10, boxShadow: '0 14px 34px rgba(24,16,80,0.13), 0 2px 6px rgba(24,16,80,0.08)', ...style}}>
    {tape ? <div style={{position: 'absolute', top: -14, left: '50%', width: 110, height: 28, marginLeft: -55, background: 'rgba(88,192,232,0.45)', transform: 'rotate(-3deg)'}} /> : null}
    {children}
  </div>
);

/** kicker + title, words rise in sequence */
export const Header: React.FC<{kicker: string; title: string; at?: number; size?: number}> = ({kicker, title, at = 0.15, size = 62}) => {
  const {t} = useScene();
  const words = title.split(' ');
  return (
    <div style={{position: 'absolute', left: 120, top: 96, right: 120}}>
      <div style={{fontFamily: F.sans, fontWeight: 700, fontSize: 22, letterSpacing: 4, color: C.blue, textTransform: 'uppercase', opacity: prog(t, at, 0.3),
        transform: `translateX(${(1 - prog(t, at, 0.4)) * -20}px)`}}>
        <span style={{display: 'inline-block', width: 34, height: 4, background: C.blue, verticalAlign: 'middle', marginRight: 14, transform: `scaleX(${prog(t, at, 0.4)})`, transformOrigin: 'left'}} />
        {kicker}
      </div>
      <div style={{fontFamily: F.sans, fontWeight: 800, fontSize: size, color: C.ink, letterSpacing: -1.2, marginTop: 10, lineHeight: 1.08}}>
        {words.map((w, i) => {
          const p = prog(t, at + 0.08 + i * 0.045, 0.45);
          return (
            <span key={i} style={{display: 'inline-block', overflow: 'hidden', verticalAlign: 'top', paddingBottom: 6}}>
              <span style={{display: 'inline-block', transform: `translateY(${(1 - p) * 100}%)`, opacity: p}}>{w}&nbsp;</span>
            </span>
          );
        })}
      </div>
    </div>
  );
};

/** sound effect placed at scene time `at` (seconds, relative to narration start of the slide) */
export const Sfx: React.FC<{at: number; name: string; vol?: number}> = ({at, name, vol = 0.12}) => {
  const {lead, mute} = useScene();
  const {fps} = useVideoConfig();
  const from = Math.max(0, Math.round((lead + at) * fps));
  if (mute) return null;
  return (
    <Sequence from={from} durationInFrames={Math.round(3 * fps)} layout="none">
      <Audio src={staticFile(`sfx/${name}.wav`)} volume={vol} />
    </Sequence>
  );
};

export const useT = () => useScene().t;
export {interpolate};

/** any hand-drawn SVG path (absolute 1920x1080 coordinates) that draws itself on */
const HandPathBase: React.FC<{d: string; at: number; len?: number; color?: string; sw?: number; dur?: number; out?: number; dash?: string}> = ({
  d, at, len = 3000, color = C.ink, sw = 4, dur = 0.6, out, dash,
}) => {
  const {t} = useScene();
  const p = prog(t, at, dur, EINOUT);
  if (p <= 0) return null;
  const o = out === undefined ? 1 : 1 - prog(t, out, 0.25);
  return (
    <svg style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', opacity: o}} width={1} height={1}>
      {dash ? (
        <path d={d} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeDasharray={dash}
          style={{clipPath: `inset(0 ${(1 - p) * 100}% 0 0)`}} />
      ) : (
        <path d={d} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={len} strokeDashoffset={len * (1 - p)} />
      )}
    </svg>
  );
};

/** rounded highlight box that pops in (for pointing at a region of a figure) */
const FocusBoxBase: React.FC<{x: number; y: number; w: number; h: number; at: number; out?: number; color?: string; fill?: string; r?: number; sw?: number}> = ({
  x, y, w, h, at, out, color = C.blue, fill = 'rgba(88,192,232,0.16)', r = 10, sw = 5,
}) => {
  const {t} = useScene();
  const p = prog(t, at, 0.3);
  const o = out === undefined ? 0 : prog(t, out, 0.25);
  if (p <= 0) return null;
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, height: h, border: `${sw}px solid ${color}`, background: fill, borderRadius: r,
      opacity: p * (1 - o), transform: `scale(${lerp(1.08, 1, p)})`}} />
  );
};

// ---------------------------------------------------------------- automatic sound effects for the motion primitives
// every primitive plays its own small sound at its cue time; pass sfx={false} to silence one
function withSfx<P extends {at: number}>(Comp: React.FC<P>, name: string, vol: number) {
  const Wrapped: React.FC<P & {sfx?: boolean}> = (props) => (
    <>
      {props.sfx === false ? null : <Sfx at={props.at} name={name} vol={vol} />}
      <Comp {...props} />
    </>
  );
  return Wrapped;
}
export const Mark = withSfx(MarkBase, 'marker', 0.04);
export const HandCircle = withSfx(HandCircleBase, 'pencil', 0.05);
export const HandArrow = withSfx(HandArrowBase, 'pencil', 0.035);
export const Note = withSfx(NoteBase, 'scribble', 0.045);
export const Counter = withSfx(CounterBase, 'counter', 0.05);
export const Stamp = withSfx(StampBase, 'stamp', 0.13);
export const Chip = withSfx(ChipBase, 'pop', 0.05);
export const HandPath = withSfx(HandPathBase, 'pencil', 0.035);
export const FocusBox = withSfx(FocusBoxBase, 'pop', 0.05);
