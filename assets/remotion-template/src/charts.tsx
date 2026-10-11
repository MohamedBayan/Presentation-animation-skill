import React from 'react';
import {Easing} from 'remotion';
import {C, F} from './theme';
import {clamp01, fmt, lerp, prog, Sfx, useScene} from './lib';

export type BarRow = {label: string; value: number; color: string; group?: string; tag?: string; tagColor?: string};
export type BarOpts = {x: number; y: number; w: number; labelW: number; min: number; max: number; rowH?: number; gap?: number; groupH?: number};

/** compute row geometry so scenes can annotate exact bars */
export function barLayout(rows: BarRow[], o: BarOpts) {
  const rowH = o.rowH ?? 34;
  const gap = o.gap ?? 12;
  const groupH = o.groupH ?? 44;
  const x0 = o.x + o.labelW + 18;
  const bw = o.w - o.labelW - 18 - 90;
  let y = o.y;
  let prev: string | undefined;
  const out: {y: number; x0: number; x1: number; h: number; groupY?: number}[] = [];
  rows.forEach((r) => {
    let groupY: number | undefined;
    if (r.group && r.group !== prev) {
      groupY = y;
      y += groupH;
    }
    prev = r.group;
    const x1 = x0 + bw * clamp01((r.value - o.min) / (o.max - o.min));
    out.push({y, x0, x1, h: rowH, groupY});
    y += rowH + gap;
  });
  return {rows: out, x0, bw, bottom: y};
}

export const HBars: React.FC<
  BarOpts & {
    rows: BarRow[];
    at: number | number[]; // one start time, or one per row
    stagger?: number;
    d?: number;
    dec?: number;
    fontSize?: number;
    focus?: {at: number; keep: number[]; out?: number}[]; // dim rows not in keep
    axis?: number[];
    groupAt?: Record<string, number>;
    sfx?: boolean;
  }
> = (props) => {
  const {t} = useScene();
  const {rows, at, stagger = 0.06, d = 0.7, dec = 3, fontSize = 24, focus = [], axis, groupAt = {}} = props;
  const L = barLayout(rows, props);
  // current dimming state
  let dimSet: number[] | null = null;
  let dimP = 0;
  for (const f of focus) {
    const p = prog(t, f.at, 0.35) * (f.out === undefined ? 1 : 1 - prog(t, f.out, 0.35));
    if (p > 0) {
      dimSet = f.keep;
      dimP = p;
    }
  }
  return (
    <div style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 1080}}>
      {axis
        ? axis.map((v, i) => {
            const x = L.x0 + L.bw * clamp01((v - props.min) / (props.max - props.min));
            const t0 = Array.isArray(at) ? Math.min(...at) : at;
            return (
              <div key={i} style={{position: 'absolute', left: x, top: props.y - 10, width: 1.5, height: L.bottom - props.y + 10, background: C.line, opacity: prog(t, t0 - 0.2, 0.4)}}>
                <div style={{position: 'absolute', top: L.bottom - props.y + 14, left: -30, width: 60, textAlign: 'center', fontFamily: F.sans, fontSize: 18, color: C.grayDark}}>
                  {v.toFixed(2)}
                </div>
              </div>
            );
          })
        : null}
      {rows.map((r, i) => {
        const g = L.rows[i];
        const t0 = Array.isArray(at) ? at[i] : at + i * stagger;
        const p = prog(t, t0, d, Easing.bezier(0.2, 0.75, 0.25, 1));
        const lp = prog(t, t0 - 0.1, 0.3);
        const dim = dimSet && !dimSet.includes(i) ? lerp(1, 0.28, dimP) : 1;
        const xe = lerp(g.x0, g.x1, p);
        return (
          <React.Fragment key={i}>
            {props.sfx === false ? null : <Sfx at={t0 + 0.05} name="tick" vol={0.04} />}
            {g.groupY !== undefined ? (
              <div style={{position: 'absolute', left: props.x, top: g.groupY + 6, fontFamily: F.sans, fontWeight: 800, fontSize: 20, letterSpacing: 3, color: C.blue,
                textTransform: 'uppercase', opacity: prog(t, groupAt[r.group!] ?? t0 - 0.15, 0.3)}}>
                {r.group}
              </div>
            ) : null}
            <div style={{position: 'absolute', left: props.x, top: g.y, width: props.labelW, height: g.h, display: 'flex', alignItems: 'center', justifyContent: 'flex-end',
              fontFamily: F.sans, fontWeight: 600, fontSize, color: C.ink, opacity: lp * dim, whiteSpace: 'nowrap'}}>
              {r.label}
            </div>
            <div style={{position: 'absolute', left: g.x0, top: g.y, height: g.h, width: Math.max(0, xe - g.x0), background: r.color, borderRadius: '0 5px 5px 0', opacity: dim}} />
            <div style={{position: 'absolute', left: xe + 10, top: g.y, height: g.h, display: 'flex', alignItems: 'center', fontFamily: F.sans, fontWeight: 700,
              fontSize: fontSize - 2, color: C.ink, opacity: clamp01((p - 0.4) / 0.6) * dim, fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap'}}>
              {fmt(r.value, dec, r.value >= 1000)}
              {r.tag ? (
                <span style={{marginLeft: 12, fontSize: 16, fontWeight: 800, letterSpacing: 1, color: C.white, background: r.tagColor ?? C.blue, padding: '3px 8px', borderRadius: 5}}>
                  {r.tag}
                </span>
              ) : null}
            </div>
          </React.Fragment>
        );
      })}
    </div>
  );
};

/** legend swatches */
export const Legend: React.FC<{items: {label: string; color: string}[]; at: number; x: number; y: number}> = ({items, at, x, y}) => {
  const {t} = useScene();
  return (
    <div style={{position: 'absolute', left: x, top: y, display: 'flex', gap: 26, fontFamily: F.sans, fontSize: 20, color: C.grayDark, opacity: prog(t, at, 0.4)}}>
      {items.map((it) => (
        <div key={it.label} style={{display: 'flex', alignItems: 'center', gap: 8}}>
          <div style={{width: 18, height: 18, borderRadius: 4, background: it.color}} />
          {it.label}
        </div>
      ))}
    </div>
  );
};
