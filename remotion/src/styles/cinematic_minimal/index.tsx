import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { getCaptionFontSize } from "../registry";

interface CinematicMinimalProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const CinematicMinimal: React.FC<CinematicMinimalProps> = ({
  event,
  words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = event.start + frame / fps;
  const fonts = getFontFamilies();

  // Subtle smooth cinema fade in and out
  const fadeIn = Math.min(1, frame / (fps * 0.25));
  const opacity = fadeIn * fadeOut(frame, durationInFrames, 8);

  const [firstIdx, lastIdx] =
    event.wordRange && event.wordRange.length >= 2
      ? [event.wordRange[0], event.wordRange[1]]
      : [0, words.length - 1];

  const phraseWords = words.slice(firstIdx, lastIdx + 1);
  const baseSize = getCaptionFontSize(event.captionSize, 42);
  const activeColor = event.highlightColor || "#F59E0B"; // Warm amber/gold for cinema

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        flexWrap: "wrap",
        gap: "10px",
        opacity,
        maxWidth: "92%",
        textAlign: "center",
        padding: "10px 28px",
        background: "rgba(10, 12, 18, 0.78)",
        backdropFilter: "blur(16px)",
        WebkitBackdropFilter: "blur(16px)",
        borderRadius: "9999px",
        border: "1px solid rgba(255, 255, 255, 0.12)",
        boxShadow: "0 10px 30px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1)",
      }}
    >
      {phraseWords.map((w, idx) => {
        const isSpoken = currentTime >= w.start;
        const isCurrentlyActive = currentTime >= w.start && currentTime <= w.end;

        const color = isCurrentlyActive
          ? activeColor
          : isSpoken
          ? "#FFFFFF"
          : "rgba(255, 255, 255, 0.65)";

        return (
          <span
            key={w.i ?? idx}
            style={{
              display: "inline-block",
              fontFamily: fonts.sans,
              fontSize: `${baseSize}px`,
              fontWeight: 600,
              letterSpacing: "0.06em",
              lineHeight: 1.2,
              color,
              textShadow: isCurrentlyActive
                ? `0 0 14px ${activeColor}88`
                : "none",
              transform: isCurrentlyActive ? "scale(1.04)" : "scale(1)",
              transition: "all 0.1s ease",
            }}
          >
            {w.text}
          </span>
        );
      })}
    </div>
  );
};
