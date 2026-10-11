import React from 'react';
import {C} from './theme';

type P = {size?: number; color?: string; style?: React.CSSProperties};
const S: React.FC<P & {children: React.ReactNode; vb?: string}> = ({size = 40, color = C.ink, style, children, vb = '0 0 48 48'}) => (
  <svg width={size} height={size} viewBox={vb} style={{display: 'inline-block', verticalAlign: 'middle', ...style}} fill="none" stroke={color} strokeWidth={3.2}
    strokeLinecap="round" strokeLinejoin="round">
    {children}
  </svg>
);

export const IPerson: React.FC<P> = (p) => (
  <S {...p}>
    <circle cx="24" cy="15" r="8" />
    <path d="M9 42c1-9 7-14 15-14s14 5 15 14" />
  </S>
);
export const IText: React.FC<P> = (p) => (
  <S {...p}>
    <rect x="9" y="6" width="30" height="36" rx="3" />
    <path d="M15 16h18M15 23h18M15 30h12" />
  </S>
);
export const IImage: React.FC<P> = (p) => (
  <S {...p}>
    <rect x="6" y="9" width="36" height="30" rx="3" />
    <circle cx="17" cy="19" r="3.5" />
    <path d="M8 35l10-10 8 8 6-6 9 9" />
  </S>
);
export const ITarget: React.FC<P> = (p) => (
  <S {...p}>
    <circle cx="24" cy="24" r="17" />
    <circle cx="24" cy="24" r="10" />
    <circle cx="24" cy="24" r="3" fill={p.color ?? C.ink} />
  </S>
);
export const IGlobe: React.FC<P> = (p) => (
  <S {...p}>
    <circle cx="24" cy="24" r="17" />
    <path d="M7 24h34M24 7c6 6 6 28 0 34M24 7c-6 6-6 28 0 34" />
  </S>
);
export const IWarn: React.FC<P> = (p) => (
  <S {...p}>
    <path d="M24 6L44 41H4z" />
    <path d="M24 19v11M24 35v.5" />
  </S>
);
export const ICheck: React.FC<P> = (p) => (
  <S {...p}>
    <path d="M10 25l9 9 19-20" />
  </S>
);
export const ICross: React.FC<P> = (p) => (
  <S {...p}>
    <path d="M13 13l22 22M35 13L13 35" />
  </S>
);
export const IUnlock: React.FC<P> = (p) => (
  <S {...p}>
    <rect x="9" y="21" width="30" height="21" rx="3" />
    <path d="M16 21v-6a8 8 0 0 1 15-3" />
  </S>
);
export const ISpark: React.FC<P> = (p) => (
  <S {...p}>
    <path d="M24 5c2 10 9 17 19 19-10 2-17 9-19 19-2-10-9-17-19-19 10-2 17-9 19-19z" />
  </S>
);
export const IFusion: React.FC<P> = (p) => (
  <S {...p}>
    <path d="M8 12h12l8 12-8 12H8M40 24H28" />
  </S>
);
export const IChat: React.FC<P> = (p) => (
  <S {...p}>
    <path d="M7 10h34v22H22l-9 8v-8H7z" />
    <path d="M15 19h18M15 25h11" />
  </S>
);
export const ILock: React.FC<P> = (p) => (
  <S {...p}>
    <rect x="9" y="21" width="30" height="21" rx="3" />
    <path d="M16 21v-6a8 8 0 0 1 16 0v6" />
  </S>
);
export const ISearch: React.FC<P> = (p) => (
  <S {...p}>
    <circle cx="21" cy="21" r="12" />
    <path d="M30 30l11 11" />
  </S>
);
export const IStack: React.FC<P> = (p) => (
  <S {...p}>
    <path d="M24 6l18 9-18 9-18-9z" />
    <path d="M6 24l18 9 18-9M6 33l18 9 18-9" />
  </S>
);
/** image post: picture with a caption line (social posts, screenshots, examples) */
export const IPost: React.FC<P> = (p) => (
  <S {...p}>
    <rect x="6" y="6" width="36" height="36" rx="3" />
    <path d="M11 13h26" />
    <circle cx="18" cy="26" r="4" />
    <path d="M8 40l12-9 8 6 6-5 8 6" />
  </S>
);
