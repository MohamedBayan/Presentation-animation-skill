import React from 'react';
import {AbsoluteFill} from 'remotion';
import pointsData from '../data/slide_points.json';
import P from '../data/project.json';
import {C, F} from '../theme';
import {Card, Counter, Header, Mark, Note, Rise, Stamp, useScene, Word, wordAt} from '../lib';
import * as Icons from '../icons';

/**
 * Generic scene WITHOUT a slide image (talks recorded with no deck, or slides you would rather re-typeset).
 * src/data/slide_points.json, keyed by slide number:
 * {
 *   "3": {
 *     "kicker": "Dataset", "title": "12,000 questions, three annotators each",
 *     "points": [
 *       {"text": "Collected from four public forums", "at": "collected", "icon": "IGlobe"},
 *       {"text": "Every item labeled by three trained annotators", "at": "three annotators", "mark": "three trained annotators"}
 *     ],
 *     "big":  {"value": 12000, "label": "labeled questions", "at": "12,000", "suffix": ""},
 *     "stamp": {"text": "Public release", "at": "publicly"},
 *     "note": {"text": "not human-verified", "at": "automatic labels"}
 *   }
 * }
 * Every "at" is a spoken phrase from THIS slide's transcript (add "occ" for a later occurrence) or seconds.
 * Missing entry: the slide shows its section name and its first spoken sentence, so nothing is ever blank.
 * Write only facts the speaker says or the deck shows (keep a facts list, see references/animation-design.md).
 */
type Pt = {text: string; at?: string | number; occ?: number; icon?: string; mark?: string};
type Spec = {kicker?: string; title?: string; points?: Pt[]; big?: {value: number; label?: string; at?: string | number; prefix?: string; suffix?: string; dec?: number};
  stamp?: {text: string; at?: string | number}; note?: {text: string; at?: string | number}};

const proj = P as any;
const when = (words: Word[], v: string | number | undefined, occ: number, fb: number) => {
  if (typeof v === 'number') return v;
  if (!v) return fb;
  try {
    return wordAt(words, v, occ);
  } catch {
    return fb;
  }
};
const firstSentence = (words: Word[]) => {
  const out: string[] = [];
  for (const w of words) {
    out.push(w.w.trim());
    if (/[.?!]$/.test(w.w.trim()) || out.length >= 14) break;
  }
  return out.join(' ');
};
const sectionName = (n: number) => {
  let name = '';
  for (const s of proj.sections ?? []) if (n >= s.from) name = s.name;
  return name;
};

/** highlight `mark` inside `text` with a marker sweep */
const Marked: React.FC<{text: string; mark?: string; at: number}> = ({text, mark, at}) => {
  if (!mark) return <>{text}</>;
  const i = text.toLowerCase().indexOf(mark.toLowerCase());
  if (i < 0) return <>{text}</>;
  return (
    <>
      {text.slice(0, i)}
      <Mark at={at}>{text.slice(i, i + mark.length)}</Mark>
      {text.slice(i + mark.length)}
    </>
  );
};

export const PointsScene: React.FC = () => {
  const {n, words, dur} = useScene();
  const spec: Spec = ((pointsData as any)[String(n)] ?? {}) as Spec;
  const pts = spec.points ?? [];
  const hasSide = !!spec.big || !!spec.stamp;
  const colW = hasSide ? 1060 : 1680;
  const spread = (i: number) => 0.9 + (i * Math.max(1, dur - 2)) / Math.max(1, pts.length + 1); // fallback timing: spread over the clip
  return (
    <AbsoluteFill>
      <Header kicker={spec.kicker ?? sectionName(n) ?? ''} title={spec.title ?? firstSentence(words)} size={spec.title && spec.title.length > 48 ? 54 : 62} />
      <div style={{position: 'absolute', left: 120, top: 300, width: colW, display: 'flex', flexDirection: 'column', gap: 26}}>
        {pts.map((p, i) => {
          const t0 = when(words, p.at, p.occ ?? 0, spread(i));
          const Ico = p.icon ? (Icons as any)[p.icon] : null;
          return (
            <Rise key={i} at={t0} dx={-30} dy={0}>
              <Card style={{display: 'flex', alignItems: 'center', gap: 26, padding: '24px 32px'}}>
                <div style={{width: 64, height: 64, borderRadius: 14, background: C.blueSoft, display: 'flex', alignItems: 'center', justifyContent: 'center', flex: '0 0 64px'}}>
                  {Ico ? <Ico size={40} color={C.blue} /> : <span style={{fontFamily: F.sans, fontWeight: 900, fontSize: 30, color: C.blue}}>{i + 1}</span>}
                </div>
                <div style={{fontFamily: F.sans, fontSize: 36, fontWeight: 600, color: C.ink, lineHeight: 1.25}}>
                  <Marked text={p.text} mark={p.mark} at={t0 + 0.5} />
                </div>
              </Card>
            </Rise>
          );
        })}
      </div>
      {spec.big ? (
        <Rise at={when(words, spec.big.at, 0, 1)} style={{position: 'absolute', left: 1260, top: 330, width: 540, textAlign: 'center'}}>
          <div style={{fontFamily: F.sans, fontWeight: 900, fontSize: 150, color: C.blue, letterSpacing: -5, lineHeight: 1}}>
            <Counter at={when(words, spec.big.at, 0, 1)} to={spec.big.value} dec={spec.big.dec ?? 0} prefix={spec.big.prefix} suffix={spec.big.suffix} />
          </div>
          {spec.big.label ? <div style={{fontFamily: F.sans, fontWeight: 700, fontSize: 34, color: C.ink, marginTop: 12}}>{spec.big.label}</div> : null}
        </Rise>
      ) : null}
      {spec.stamp ? (
        <div style={{position: 'absolute', left: 1300, top: spec.big ? 640 : 420}}>
          <Stamp at={when(words, spec.stamp.at, 0, dur - 2)} color={C.good} size={34}>
            {spec.stamp.text}
          </Stamp>
        </div>
      ) : null}
      {spec.note ? (
        <Note at={when(words, spec.note.at, 0, dur - 2)} x={hasSide ? 1280 : 1180} y={850} size={46} color={C.bad} rot={-3}>
          {spec.note.text}
        </Note>
      ) : null}
    </AbsoluteFill>
  );
};
