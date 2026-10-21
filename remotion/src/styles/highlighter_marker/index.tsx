import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { getCaptionFontSize } from "../registry";

interface HighlighterMarkerProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const HighlighterMarker: React.FC<HighlighterMarkerProps> = ({
  event,
  words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = event.start + frame / fps;
  const fonts = getFontFamilies();

  const scale = popIn(frame, fps, 0, 14, 0.5, 160);
  const opacity = fadeOut(frame, durationInFrames, 6);

  const [firstIdx, lastIdx] =
    event.wordRange && event.wordRange.length >= 2
      ? [event.wordRange[0], event.wordRange[1]]
      : [0, words.length - 1];

  const phraseWords = words.slice(firstIdx, lastIdx + 1);
  const baseSize = getCaptionFontSize(event.captionSize, 48);
  const markerColor = event.highlightColor || "#FEF08A"; // Soft pastel highlighter yellow

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
        maxWidth: "90%",
        textAlign: "center",
        padding: "8px 16px",
      }}
    >
      {phraseWords.map((w, idx) => {
        const isSpoken = currentTime >= w.start;
        const isCurrentlyActive = currentTime >= w.start && currentTime <= w.end;

        return (
          <span
            key={w.i ?? idx}
            style={{
              position: "relative",
              display: "inline-block",
              fontFamily: fonts.sans,
              fontSize: `${baseSize}px`,
              fontWeight: 800,
              letterSpacing: "-0.01em",
              lineHeight: 1.25,
              color: isCurrentlyActive ? "#090A0F" : "#FFFFFF",
              textShadow: isCurrentlyActive
                ? "none"
                : "0 2px 8px rgba(0,0,0,0.85), 0 1px 2px rgba(0,0,0,0.9)",
              padding: "2px 6px",
              borderRadius: "6px",
              zIndex: 1,
              transition: "color 0.1s ease",
            }}
          >
            {/* Realistic marker highlight sweep layer */}
            {isSpoken && (
              <span
                style={{
                  position: "absolute",
                  inset: "10% -2px 10% -2px",
                  background: isCurrentlyActive
                    ? markerColor
                    : `${markerColor}33`,
                  borderRadius: "4px",
                  transform: "rotate(-1deg)",
                  zIndex: -1,
                  boxShadow: isCurrentlyActive
                    ? `0 2px 12px ${markerColor}99`
                    : "none",
                  transition: "all 0.12s ease",
                }}
              />
            )}
            {w.text}
          </span>
        );
      })}
    </div>
  );
};
