import React from 'react';
import P from '../data/project.json';
import points from '../data/slide_points.json';
import images from '../data/slide_images.json';
import {PointsScene} from './PointsScene';
import {SlideScene} from './SlideScene';
import {TitleScene} from './TitleScene';

/**
 * Custom scenes, keyed by SLIDE NUMBER. Add your own here, e.g.
 *   import {S04} from './S04';
 *   export const CUSTOM: Record<number, React.FC> = {4: S04};
 * Every slide without a custom scene falls back to, in order:
 *   - TitleScene for the first slide when project.json has "authors" (animated title card from project.json)
 *   - PointsScene when src/data/slide_points.json has an entry for the slide (re-typeset kicker/title/points/number)
 *   - SlideScene when the deck gave a rendered image (slide image + cues from src/data/slide_cues.json)
 *   - PointsScene otherwise (section name + first spoken sentence; write slide_points.json to do better)
 */
export const CUSTOM: Record<number, React.FC> = {};

export const sceneFor = (n: number, index: number): React.FC => {
  if (CUSTOM[n]) return CUSTOM[n];
  if (index === 0 && (P as any).authors) return TitleScene;
  if ((points as any)[String(n)]) return PointsScene;
  if ((images as number[]).includes(n)) return SlideScene;
  return PointsScene;
};
