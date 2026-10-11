import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {C, F} from '../theme';
import {At, Card, Chip, Counter, EINOUT, FocusBox, HandArrow, HandCircle, Header, Mark, Note, prog, Rise, Sfx, Stamp, useAt, useScene} from '../lib';
import {barLayout, BarRow, HBars, Legend} from '../charts';
import {ICheck, ICross, IPerson, IStack, ITarget} from '../icons';

/**
 * Recipe scenes for the full (Vox-style) tier, written for a FICTIONAL talk ("TinyQA").
 * Every name, number and phrase below is a placeholder. When you reuse a recipe:
 *   1. copy it into W/remotion/src/scenes/ and register it in CUSTOM (src/scenes/index.ts) under the slide number;
 *   2. replace the data with the deck's real values and log each one in W/facts.md;
 *   3. replace every at('...') phrase with a phrase the speaker actually says on that slide (W/transcripts/cut/recNN.txt).
 * Layout: 1920x1080, margins 120 px, content between y 260 and 940 (captions live below).
 */

// ===================================================================== Contribution: a row of big numbers
export const Contribution: React.FC = () => {
  const {t} = useScene();
  const at = useAt();
  const tParts = at('four parts');
  const tN = at('12,000');
  const tAnn = at('three annotators');
  const tCat = at('eight categories');
  const tFam = at('three model families');
  const tPub = at('publicly');
  const X = [120, 555, 990, 1425];
  const big: React.CSSProperties = {fontFamily: F.sans, fontWeight: 900, fontSize: 118, color: C.ink, letterSpacing: -3, lineHeight: 1};
  const lab: React.CSSProperties = {fontFamily: F.sans, fontWeight: 800, fontSize: 36, color: C.blue, marginTop: 6};
  const body: React.CSSProperties = {fontFamily: F.sans, fontSize: 24, color: C.ink, lineHeight: 1.4, marginTop: 20};
  const cols = [
    {at: tN, to: 12000, label: 'questions', body: <>labeled by <b>three annotators</b></>, icons: true},
    {at: tCat, to: 8, label: 'categories', body: <>a two-level taxonomy</>},
    {at: tFam, to: 3, label: 'model families', body: <>zero-shot, few-shot and fine-tuned</>},
  ];
  return (
    <AbsoluteFill>
      <Header kicker="Overview" title="Our contribution" />
      {[0, 1, 2].map((i) => (
        <div key={i} style={{position: 'absolute', left: X[i + 1] - 34, top: 270, width: 2, height: 560 * prog(t, tParts + 0.1 * i, 0.6, EINOUT), background: C.line}} />
      ))}
      {cols.map((c, i) => (
        <At key={i} x={X[i]} y={300} w={380}>
          <Rise at={c.at - 0.1} style={big}>
            <Counter at={c.at - 0.1} to={c.to} d={c.to > 100 ? 1.0 : 0.6} />
          </Rise>
          <Rise at={c.at + 0.4} style={lab}>{c.label}</Rise>
          <Rise at={c.at + 0.7} style={body}>{c.body}</Rise>
          {c.icons ? (
            <div style={{display: 'flex', gap: 6, marginTop: 10}}>
              {[0, 1, 2].map((k) => (
                <Rise key={k} at={tAnn + k * 0.12} dy={14}>
                  <IPerson size={56} color={C.ink} />
                </Rise>
              ))}
            </div>
          ) : null}
        </At>
      ))}
      <At x={X[3]} y={330} w={380}>
        <Stamp at={tPub} color={C.good} size={34}>Public release</Stamp>
        <Rise at={tPub + 0.5} style={body}>data, guidelines and evaluation code</Rise>
      </At>
      <Sfx at={tParts} name="thud" vol={0.07} />
    </AbsoluteFill>
  );
};

// ===================================================================== RelatedWork: rebuilt table, own row last
const PRIOR = [
  ['QA-Small', '2019', '3,100', false],
  ['ForumQA', '2021', '6,400', false],
  ['MultiAsk', '2023', '9,800', true],
] as const;

export const RelatedWork: React.FC = () => {
  const at = useAt();
  const tPrior = at('prior datasets');
  const tNone = at('none of them');
  const tOurs = at('our dataset');
  const cols = [140, 760, 1060, 1500];
  const rowY = (i: number) => 384 + i * 64;
  return (
    <AbsoluteFill>
      <Header kicker="Related work" title="What existing datasets cover" />
      <Rise at={tPrior - 0.3} style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 1080}}>
        {['Dataset', 'Year', 'Size', 'Fine-grained labels'].map((h, i) => (
          <div key={h} style={{position: 'absolute', left: cols[i], top: 336, fontFamily: F.sans, fontSize: 19, fontWeight: 800, letterSpacing: 2.5, color: C.blue,
            textTransform: 'uppercase', whiteSpace: 'nowrap'}}>
            {h}
          </div>
        ))}
        <div style={{position: 'absolute', left: 130, top: 372, width: 1660, height: 2, background: C.ink, opacity: 0.6}} />
      </Rise>
      {PRIOR.map((r, i) => (
        <Rise key={i} at={tPrior + i * 0.18} dx={40} dy={0} style={{position: 'absolute', left: 0, top: rowY(i), width: 1920, height: 64}}>
          <div style={{position: 'absolute', left: 130, top: 63, width: 1660, height: 1, background: C.line}} />
          {r.slice(0, 3).map((v, k) => (
            <div key={k} style={{position: 'absolute', left: cols[k], top: 16, fontFamily: F.sans, fontSize: 26, color: C.ink, fontWeight: k === 0 ? 700 : 400,
              fontVariantNumeric: 'tabular-nums'}}>
              {v as string}
            </div>
          ))}
          <div style={{position: 'absolute', left: cols[3] + 10, top: 12}}>{r[3] ? <ICheck size={36} color={C.good} /> : <ICross size={30} color={C.gray} />}</div>
        </Rise>
      ))}
      <Rise at={tOurs} dx={90} dy={0} from={1} style={{position: 'absolute', left: 0, top: rowY(3) + 8, width: 1920, height: 70}}>
        <div style={{position: 'absolute', left: 124, top: 0, width: 1672, height: 70, background: C.blue, borderRadius: 8}} />
        {['TinyQA (ours)', '2026', '12,000'].map((v, k) => (
          <div key={k} style={{position: 'absolute', left: cols[k], top: 17, fontFamily: F.sans, fontSize: 27, color: C.white, fontWeight: 800}}>{v}</div>
        ))}
        <div style={{position: 'absolute', left: cols[3] + 10, top: 14}}>
          <ICheck size={40} color={C.white} />
        </div>
      </Rise>
      <HandCircle x={cols[3] - 30} y={rowY(0) - 6} w={200} h={3 * 64 + 4} at={tNone} color={C.bad} sw={5} />
      <Note at={tNone + 0.5} x={cols[3] + 190} y={rowY(1)} size={46} color={C.bad} rot={-3}>only one</Note>
      {PRIOR.map((_, i) => (
        <Sfx key={i} at={tPrior + 0.05 + i * 0.18} name="tick" vol={0.04} />
      ))}
      <Sfx at={tOurs} name="whoosh_soft" vol={0.06} />
      <Sfx at={tOurs + 0.25} name="thud" vol={0.09} />
    </AbsoluteFill>
  );
};

// ===================================================================== FigureWalkthrough: a deck figure, regions in spoken order
// The deck's own figure (W/deck/slideNN.png, or a crop of it in public/img/) shown in a card; regions are pixel boxes on the
// displayed image. Use this when a diagram is too complex to rebuild.
const FIG = {src: 'slides/slide05.png', x: 120, y: 260, w: 1180, h: 664};
const STEPS = [
  {phrase: 'we collect', x: 0.03, y: 0.25, w: 0.27, h: 0.5, label: 'collect'},
  {phrase: 'filter', x: 0.36, y: 0.25, w: 0.27, h: 0.5, label: 'filter'},
  {phrase: 'annotate', x: 0.69, y: 0.25, w: 0.28, h: 0.5, label: 'annotate'},
];

export const FigureWalkthrough: React.FC = () => {
  const at = useAt();
  const tTotal = at('in total');
  const ts = STEPS.map((s) => at(s.phrase));
  const px = (f: number) => FIG.x + f * FIG.w;
  const py = (f: number) => FIG.y + f * FIG.h;
  return (
    <AbsoluteFill>
      <Header kicker="Method" title="How the data was built" />
      <Rise at={0.2} style={{position: 'absolute', left: FIG.x - 12, top: FIG.y - 12}}>
        <Card style={{padding: 12}}>
          <Img src={staticFile(FIG.src)} style={{width: FIG.w, height: FIG.h, display: 'block'}} />
        </Card>
      </Rise>
      {STEPS.map((s, i) => (
        <React.Fragment key={i}>
          <FocusBox at={ts[i]} x={px(s.x)} y={py(s.y)} w={s.w * FIG.w} h={s.h * FIG.h} color={C.blue} sw={4} fill="rgba(0,136,200,0.06)" r={8} />
          {i > 0 ? <HandArrow at={ts[i] - 0.2} x1={px(STEPS[i - 1].x + STEPS[i - 1].w) - 10} y1={py(s.y) - 30} x2={px(s.x) + 20} y2={py(s.y) - 30} bend={-0.3} /> : null}
          <Chip at={ts[i] + 0.2} size={24} style={{position: 'absolute', left: px(s.x), top: py(s.y + s.h) + 14}}>
            {`${i + 1}. ${s.label}`}
          </Chip>
        </React.Fragment>
      ))}
      <At x={1380} y={380} w={420}>
        <Rise at={tTotal - 0.1} style={{fontFamily: F.sans, fontWeight: 900, fontSize: 120, color: C.blue, letterSpacing: -4, lineHeight: 1}}>
          <Counter at={tTotal - 0.1} to={12000} />
        </Rise>
        <Rise at={tTotal + 0.4} style={{fontFamily: F.sans, fontSize: 30, fontWeight: 700, color: C.ink, marginTop: 8}}>labeled questions</Rise>
      </At>
    </AbsoluteFill>
  );
};

// ===================================================================== MainResult: bars grow, focus on the best, delta as a number
const ROWS: BarRow[] = [
  {label: 'Model C, fine-tuned', value: 0.81, color: C.blue},
  {label: 'Model B, fine-tuned', value: 0.77, color: C.blue},
  {label: 'Model C, 5-shot', value: 0.74, color: C.cyan},
  {label: 'Model A, zero-shot', value: 0.69, color: C.gray},
  {label: 'Model C, zero-shot', value: 0.66, color: C.gray},
];
const OPTS = {x: 120, y: 280, w: 1190, labelW: 380, min: 0.5, max: 0.9, rowH: 46, gap: 16};

export const MainResult: React.FC = () => {
  const at = useAt();
  const tCompare = at('we compare');
  const tBest = at('the best');
  const tPoints = at('points');
  const tZero = at('zero-shot');
  const L = barLayout(ROWS, OPTS);
  const r0 = L.rows[0];
  return (
    <AbsoluteFill>
      <Header kicker="Results" title="Fine-tuning gives the best model" />
      <HBars rows={ROWS} {...OPTS} at={tCompare} stagger={0.08} dec={2} fontSize={24} axis={[0.5, 0.6, 0.7, 0.8, 0.9]}
        focus={[{at: tBest, keep: [0], out: tZero}, {at: tZero, keep: [3, 4]}]} />
      <Legend at={tCompare + 0.6} x={120 + 398} y={L.bottom + 40} items={[{label: 'fine-tuned', color: C.blue}, {label: 'few-shot', color: C.cyan}, {label: 'zero-shot', color: C.gray}]} />
      <HandCircle x={r0.x1 - 14} y={r0.y - 14} w={124} h={r0.h + 28} at={tBest + 0.1} out={tZero} color={C.bad} sw={5} />
      <At x={1400} y={300} w={410}>
        <Rise at={tPoints - 0.2} style={{fontFamily: F.sans, fontWeight: 900, fontSize: 120, color: C.blue, letterSpacing: -4, lineHeight: 1}}>
          <Counter at={tPoints - 0.2} to={15} prefix="+" d={0.8} />
        </Rise>
        <Rise at={tPoints + 0.2} style={{fontFamily: F.sans, fontSize: 26, color: C.ink, lineHeight: 1.35, marginTop: 8}}>
          points over the same model zero-shot
        </Rise>
        <Rise at={tPoints + 0.5} style={{fontFamily: F.sans, fontSize: 34, fontWeight: 800, color: C.ink, marginTop: 10, fontVariantNumeric: 'tabular-nums'}}>
          0.66 → 0.81
        </Rise>
      </At>
      <Sfx at={tBest - 0.8} name="riser" vol={0.05} />
      <Sfx at={tPoints + 0.5} name="chime" vol={0.06} />
    </AbsoluteFill>
  );
};

// ===================================================================== Takeaways: numbered cards + a "Next" panel
export const Takeaways: React.FC = () => {
  const at = useAt();
  const cards = [
    {at: at('first'), h: <>A <Mark at={at('benchmark')}>fine-grained benchmark</Mark> for small-data QA.</>, s: '12,000 questions, eight categories, public.'},
    {at: at('second'), h: 'If you have labels, fine-tune.', s: 'Fine-tuning beats prompting by a wide margin.'},
    {at: at('third'), h: 'Zero-shot models miss the rare categories.', s: <>Few-shot examples <Mark at={at('only part')} color={C.badSoft}>close only part of the gap</Mark>.</>},
  ];
  const next = [
    {at: at('more languages'), s: 'More languages'},
    {at: at('harder questions'), s: 'Harder, multi-step questions'},
  ];
  const tNext = next[0].at - 0.4;
  return (
    <AbsoluteFill>
      <Header kicker="Conclusion" title="Takeaways" />
      {cards.map((c, i) => (
        <At key={i} x={120} y={270 + i * 210} w={1140}>
          <Rise at={c.at - 0.1} dy={30}>
            <Card style={{display: 'flex', gap: 28, alignItems: 'center', padding: '22px 30px'}}>
              <div style={{fontFamily: F.sans, fontWeight: 900, fontSize: 70, color: C.blue, lineHeight: 1, width: 54}}>{i + 1}</div>
              <div>
                <div style={{fontFamily: F.sans, fontWeight: 800, fontSize: 32, color: C.ink, lineHeight: 1.25}}>{c.h}</div>
                <div style={{fontFamily: F.sans, fontSize: 24, color: C.grayDark, marginTop: 8, lineHeight: 1.4}}>{c.s}</div>
              </div>
            </Card>
          </Rise>
          <Sfx at={c.at - 0.1} name="paper" vol={0.07} />
        </At>
      ))}
      <At x={1340} y={270} w={460}>
        <Rise at={tNext} dx={40} dy={0}>
          <div style={{height: 610, background: C.ink, borderRadius: 12, padding: '28px 30px', boxSizing: 'border-box'}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 12, fontFamily: F.sans, fontWeight: 800, fontSize: 22, letterSpacing: 4, color: C.cyan, textTransform: 'uppercase'}}>
              <ITarget size={30} color={C.cyan} /> Next
            </div>
            {next.map((x, i) => (
              <Rise key={i} at={x.at} dx={-20} dy={0} style={{display: 'flex', gap: 14, marginTop: 30, fontFamily: F.sans, fontSize: 28, fontWeight: 700, color: C.white}}>
                <span style={{color: C.cyan, fontWeight: 900}}>→</span>
                <span>{x.s}</span>
              </Rise>
            ))}
          </div>
        </Rise>
      </At>
      <Sfx at={tNext} name="whoosh_soft" vol={0.06} />
    </AbsoluteFill>
  );
};

// ===================================================================== Thanks: dark page, contact, QR code from the deck
// The QR image is cropped from the deck's last slide (never generate a QR for a URL you have not verified with the user).
export const Thanks: React.FC = () => {
  const {t} = useScene();
  const at = useAt();
  const tCode = at('code');
  const p = prog(t, tCode, 0.5);
  return (
    <AbsoluteFill>
      <Img src={staticFile('img/paper_dark.png')} style={{position: 'absolute', inset: 0, width: 1920, height: 1080}} />
      <At x={120} y={180} style={{fontFamily: F.sans, fontWeight: 900, fontSize: 150, color: C.white, letterSpacing: -5, lineHeight: 1}}>
        {'Thank you'.split(' ').map((w, i) => {
          const q = prog(t, 0.2 + i * 0.15, 0.5);
          return (
            <span key={i} style={{display: 'inline-block', transform: `translateY(${(1 - q) * 60}px)`, opacity: q, marginRight: 34}}>
              {w}
            </span>
          );
        })}
      </At>
      <Rise at={0.6} style={{position: 'absolute', left: 124, top: 370, fontFamily: F.sans, fontWeight: 700, fontSize: 52, color: C.cyan}}>Questions?</Rise>
      <Rise at={0.9} style={{position: 'absolute', left: 124, top: 490, fontFamily: F.sans, fontWeight: 800, fontSize: 36, color: C.white}}>Speaker Name</Rise>
      <Rise at={1.0} style={{position: 'absolute', left: 124, top: 540, fontFamily: F.sans, fontSize: 30, color: C.cyan}}>name@institution.edu</Rise>
      <div style={{position: 'absolute', left: 1360, top: 300, width: 330, opacity: p, transform: `perspective(900px) rotateY(${(1 - p) * 70}deg)`}}>
        <div style={{background: C.white, borderRadius: 12, padding: 18}}>
          <div style={{width: 294, height: 294, background: C.line, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <IStack size={90} color={C.grayDark} />
          </div>
          <div style={{fontFamily: F.sans, fontWeight: 800, fontSize: 18, letterSpacing: 3, color: C.blue, marginTop: 12, textTransform: 'uppercase'}}>Code and data</div>
        </div>
      </div>
      <Sfx at={0.25} name="thud" vol={0.08} />
      <Sfx at={tCode} name="swish" vol={0.05} />
    </AbsoluteFill>
  );
};
