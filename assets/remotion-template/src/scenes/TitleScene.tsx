import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import P from '../data/project.json';
import {C, F} from '../theme';
import {At, EINOUT, lerp, Mark, prog, Rise, Sfx, useScene, wordAt} from '../lib';
import {IWarn} from '../icons';

/**
 * Animated title card built from project.json:
 *   short_title ("TinyQA"), title ("TinyQA: A Small Benchmark for ..."; the part after ':' becomes the subtitle),
 *   authors (string), affiliations (string or list), venue ("ACL 2026"), co_located (one line),
 *   logos.top_left / top_right / bottom (files copied to public/img/logos by make_assets.py),
 *   content_warning (text) + content_warning_at (spoken phrase when it should appear).
 * Replace it with a custom scene for more (see examples/sample-talk/scenes/Recipes.tsx).
 */
const proj = P as any;
const logo = (f: string) => staticFile('img/logos/' + f.split(/[\\/]/).pop());
const asList = (v: any): string[] => (Array.isArray(v) ? v : v ? [v] : []);

const Motif: React.FC = () => {
  const {t} = useScene();
  const cols = [C.blue, C.cyan, C.ink, C.blueSoft];
  const tiles = [];
  for (let r = 0; r < 4; r++)
    for (let c = 0; c < 4; c++) {
      const k = r * 4 + c;
      const flip = (k * 5) % 3 === 0;
      const p = prog(t, 0.35 + (r + c) * 0.06, 0.6);
      tiles.push(
        <div key={k} style={{position: 'absolute', left: c * 128, top: r * 128, width: 120, height: 120, opacity: p, transform: `rotate(${(1 - p) * 90}deg) scale(${lerp(0.5, 1, p)})`}}>
          <svg width={120} height={120}>
            <polygon points={flip ? '0,0 120,0 0,120' : '0,0 120,0 120,120'} fill={cols[(k * 7 + r) % 4]} />
            <polygon points={flip ? '120,0 120,120 0,120' : '0,0 0,120 120,120'} fill={cols[(k * 3 + c + 1) % 4]} />
          </svg>
        </div>,
      );
    }
  return <At x={1300} y={190}>{tiles}</At>;
};

export const TitleScene: React.FC = () => {
  const {t, words} = useScene();
  const big: string = proj.short_title ?? '';
  const full: string = proj.title ?? '';
  const sub = full.includes(':') ? full.split(':').slice(1).join(':').trim() : full === big ? '' : full;
  let tWarn = 1.2;
  try {
    if (proj.content_warning_at) tWarn = wordAt(words, proj.content_warning_at);
  } catch {}
  const split = Math.max(1, Math.ceil(big.length / 3));
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', left: 120, top: 44, height: 110, display: 'flex', alignItems: 'center', gap: 40}}>
        {asList(proj.logos?.top_left).map((f, i) => (
          <Rise key={f} at={0.1 + i * 0.1}>
            <Img src={logo(f)} style={{height: 92, display: 'block'}} />
          </Rise>
        ))}
      </div>
      <div style={{position: 'absolute', right: 120, top: 36, height: 124, display: 'flex', alignItems: 'center', gap: 46}}>
        {asList(proj.logos?.top_right).map((f, i) => (
          <Rise key={f} at={0.25 + i * 0.12} dy={14}>
            <Img src={logo(f)} style={{height: 96, display: 'block'}} />
          </Rise>
        ))}
      </div>
      <Motif />
      <At x={112} y={214} style={{fontFamily: F.sans, fontWeight: 900, fontSize: big.length > 12 ? 130 : 176, letterSpacing: -6, lineHeight: 1, whiteSpace: 'nowrap'}}>
        {big.split('').map((ch, i) => {
          const p = prog(t, 0.3 + i * 0.035, 0.5);
          return (
            <span key={i} style={{display: 'inline-block', transform: `translateY(${(1 - p) * 70}px)`, opacity: p, color: i < split ? C.blue : C.ink}}>
              {ch === ' ' ? ' ' : ch}
            </span>
          );
        })}
      </At>
      <div style={{position: 'absolute', left: 120, top: 404, height: 12, width: 1010 * prog(t, 1.0, 0.55, EINOUT), background: C.cyan}} />
      {sub ? (
        <At x={120} y={440} w={1120} style={{fontFamily: F.sans, fontWeight: 700, fontSize: 50, color: C.ink, lineHeight: 1.2, letterSpacing: -0.5}}>
          <Rise at={0.8}>
            <Mark at={1.6} strong>
              {sub}
            </Mark>
          </Rise>
        </At>
      ) : null}
      <At x={120} y={600} w={1120} style={{fontFamily: F.sans, fontSize: 27, color: C.ink, lineHeight: 1.45}}>
        <Rise at={1.3}>{asList(proj.authors).join(', ')}</Rise>
        <Rise at={1.5} style={{fontSize: 21, color: C.grayDark, marginTop: 10, lineHeight: 1.5}}>
          {asList(proj.affiliations).map((x, i) => (
            <div key={i}>{x}</div>
          ))}
        </Rise>
      </At>
      <At x={120} y={788} style={{display: 'flex', alignItems: 'center', gap: 28}}>
        {asList(proj.logos?.bottom).map((f, i) => (
          <Rise key={f} at={1.7 + i * 0.1}>
            <Img src={logo(f)} style={{height: 60, display: 'block'}} />
          </Rise>
        ))}
        {proj.venue ? (
          <Rise at={1.85}>
            <div style={{display: 'inline-block', background: C.blue, color: C.white, fontFamily: F.sans, fontWeight: 800, fontSize: 28, padding: '9px 24px', borderRadius: 8, letterSpacing: 1}}>
              {proj.venue}
            </div>
          </Rise>
        ) : null}
        {proj.co_located ? (
          <Rise at={2.0} style={{fontFamily: F.sans, fontSize: 22, color: C.grayDark, lineHeight: 1.35, maxWidth: 520}}>
            {proj.co_located}
          </Rise>
        ) : null}
      </At>
      {proj.content_warning ? (
        <At x={120} y={884} w={1680}>
          <Rise at={tWarn} dy={40}>
            <div style={{display: 'flex', alignItems: 'center', gap: 18, background: C.badSoft, borderLeft: `8px solid ${C.bad}`, padding: '16px 26px', borderRadius: 6,
              fontFamily: F.sans, fontSize: 29, fontWeight: 700, color: C.bad}}>
              <IWarn size={40} color={C.bad} />
              {proj.content_warning}
            </div>
          </Rise>
          <Sfx at={tWarn} name="paper" vol={0.09} />
        </At>
      ) : null}
      <Sfx at={0.55} name="thud" vol={0.08} />
    </AbsoluteFill>
  );
};
