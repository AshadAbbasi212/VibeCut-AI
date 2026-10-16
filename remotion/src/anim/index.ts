import { interpolate, spring } from "remotion";

/**
 * Spring pop-in animation starting at delayFrames with slight overshoot.
 */
export const popIn = (
  frame: number,
  fps: number,
  delayFrames: number = 0,
  damping: number = 12,
  mass: number = 0.5,
  stiffness: number = 150
): number => {
  if (frame < delayFrames) return 0;
  return spring({
    frame: frame - delayFrames,
    fps,
    config: {
      damping,
      mass,
      stiffness,
    },
  });
};

/**
 * Smooth fade out over the last fadeDurationFrames of an element.
 */
export const fadeOut = (
  frame: number,
  durationInFrames: number,
  fadeDurationFrames: number = 6
): number => {
  if (durationInFrames <= fadeDurationFrames) return 1;
  const startFade = durationInFrames - fadeDurationFrames;
  if (frame < startFade) return 1;
  return interpolate(frame, [startFade, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
};

/**
 * Gentle vertical floating oscillation for stickers and graphics.
 */
export const floatY = (
  frame: number,
  fps: number,
  amplitude: number = 6,
  frequency: number = 1.5
): number => {
  const t = (frame / fps) * frequency * Math.PI * 2;
  return Math.sin(t) * amplitude;
};

/**
 * Twinkle animation for sparkle stars (scale + rotation).
 */
export const twinkle = (
  frame: number,
  fps: number,
  phaseOffset: number = 0
): { scale: number; rotation: number } => {
  const t = (frame / fps) * 3 * Math.PI * 2 + phaseOffset;
  const scale = 0.85 + Math.sin(t) * 0.25;
  const rotation = Math.sin(t * 0.5) * 15;
  return { scale, rotation };
};
