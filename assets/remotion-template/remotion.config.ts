import {Config} from '@remotion/cli/config';
// jpeg frames at q95; no OpenGL override (forcing 'angle' made render tabs hang on a Windows laptop)
Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(95);
