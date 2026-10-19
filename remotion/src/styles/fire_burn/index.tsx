import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { getCaptionFontSize } from "../registry";

interface FireBurnProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const FireBurn: React.FC<FireBurnProps> = ({
  event,
  words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = event.start + frame / fps;
  const fonts = getFontFamilies();

  const scale = popIn(frame, fps, 0, 10, 0.5, 180);
  const opacity = fadeOut(frame, durationInFrames, 5);

  const [firstIdx, lastIdx] =
    event.wordRange && event.wordRange.length >= 2
      ? [event.wordRange[0], event.wordRange[1]]
      : [0, words.length - 1];

  const phraseWords = words.slice(firstIdx, lastIdx + 1);
  const baseSize = getCaptionFontSize(event.captionSize, 54);

  // Flame flicker animation
  const flicker = 0.85 + ((frame * 7) % 5) * 0.04;

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        flexWrap: "wrap",
        gap: "10px",
        transform: `scale(${scale})`,
        opacity,
        maxWidth: "92%",
        textAlign: "center",
        padding: "6px 12px",
      }}
    >
      {phraseWords.map((w, idx) => {
        const isSpoken = currentTime >= w.start;

        return (
          <span
            key={w.i ?? idx}
            style={{
              fontFamily: fonts.sans,
              fontSize: `${baseSize}px`,
              fontWeight: 900,
              textTransform: "uppercase",
              letterSpacing: "0.03em",
              lineHeight: 1.15,
              background: isSpoken
                ? "linear-gradient(180deg, #FEF08A 0%, #F59E0B 40%, #EF4444 85%)"
                : "linear-gradient(180deg, #FFFFFF 0%, #E2E8F0 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              filter: isSpoken
                ? `drop-shadow(0 0 12px rgba(249, 115, 22, ${flicker})) drop-shadow(0 0 24px rgba(239, 68, 68, ${flicker * 0.8})) drop-shadow(0 2px 4px rgba(0,0,0,0.9))`
                : "drop-shadow(0 3px 6px rgba(0, 0, 0, 0.85))",
              WebkitTextStroke: "1px rgba(0, 0, 0, 0.4)",
              transition: "filter 0.05s ease",
            }}
          >
            {w.text}
          </span>
        );
      })}
    </div>
  );
};
