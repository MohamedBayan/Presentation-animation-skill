// Palette comes from src/data/project.json ("palette"), written by the scripts from W/project.json.
// Key names: blue = primary, cyan = accent, bad = errors / negative class (red), good = verdicts / positive (green).
import P from './data/project.json';

const pal: Record<string, string> = {
  primary: '#0088C8', ink: '#181050', accent: '#58C0E8', paper: '#F6F4EE', bad: '#C0283D', good: '#1E8576',
  ...((P as any).palette ?? {}),
};
const mix = (hex: string, t: number) => {
  const n = parseInt(hex.slice(1), 16);
  const ch = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) => Math.round(v + (255 - v) * t));
  return '#' + ch.map((v) => v.toString(16).padStart(2, '0')).join('');
};

export const C = {
  paper: pal.paper,
  ink: pal.ink,
  inkSoft: mix(pal.ink, 0.2),
  blue: pal.primary,
  cyan: pal.accent,
  cyanSoft: mix(pal.accent, 0.68),
  blueSoft: mix(pal.primary, 0.83),
  bad: pal.bad,
  badSoft: mix(pal.bad, 0.82),
  good: pal.good,
  goodSoft: mix(pal.good, 0.82),
  gray: '#A4A9B4',
  grayDark: '#5E6575',
  line: '#DCD8CD',
  white: '#FFFFFF',
  maroon: pal.extra1 ?? '#681840',
  amber: pal.warn ?? '#E3A33B',
};

export const F = {
  sans: 'Inter, "Segoe UI", system-ui, sans-serif',
  hand: 'Caveat, "Segoe Print", cursive',
  ar: 'Cairo, "Segoe UI", sans-serif',
};

export const W = 1920;
export const H = 1080;
export const MX = 120;
