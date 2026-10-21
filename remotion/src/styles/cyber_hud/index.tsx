import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { getCaptionFontSize } from "../registry";

interface CyberHudProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const CyberHud: React.FC<CyberHudProps> = ({
  event,
  words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = event.start + frame / fps;
  const fonts = getFontFamilies();

  const scale = popIn(frame, fps, 0, 10, 0.45, 180);
  const opacity = fadeOut(frame, durationInFrames, 5);

  const [firstIdx, lastIdx] =
    event.wordRange && event.wordRange.length >= 2
      ? [event.wordRange[0], event.wordRange[1]]
      : [0, words.length - 1];

  const phraseWords = words.slice(firstIdx, lastIdx + 1);
  const baseSize = getCaptionFontSize(event.captionSize, 46);
  const hudColor = event.highlightColor || "#00F5FF"; // High voltage neon cyan

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        transform: `scale(${scale})`,
        opacity,
        maxWidth: "94%",
        padding: "8px 18px",
        background: "rgba(5, 10, 20, 0.88)",
        border: `1.5px solid ${hudColor}88`,
        borderRadius: "4px",
        boxShadow: `0 0 20px ${hudColor}44, inset 0 0 12px ${hudColor}22`,
        position: "relative",
      }}
    >
      {/* Sci-fi bracket corner markers */}
      <span
        style={{
          position: "absolute",
          top: "-3px",
          left: "-3px",
          width: "8px",
          height: "8px",
          borderTop: `2px solid ${hudColor}`,
          borderLeft: `2px solid ${hudColor}`,
        }}
      />
      <span
        style={{
          position: "absolute",
          top: "-3px",
          right: "-3px",
          width: "8px",
          height: "8px",
          borderTop: `2px solid ${hudColor}`,
          borderRight: `2px solid ${hudColor}`,
        }}
      />
      <span
        style={{
          position: "absolute",
          bottom: "-3px",
          left: "-3px",
          width: "8px",
          height: "8px",
          borderBottom: `2px solid ${hudColor}`,
          borderLeft: `2px solid ${hudColor}`,
        }}
      />
      <span
        style={{
          position: "absolute",
          bottom: "-3px",
          right: "-3px",
          width: "8px",
          height: "8px",
          borderBottom: `2px solid ${hudColor}`,
          borderRight: `2px solid ${hudColor}`,
        }}
      />

      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          flexWrap: "wrap",
          gap: "10px",
          textAlign: "center",
        }}
      >
        <span
          style={{
            fontFamily: fonts.mono,
            fontSize: `${Math.round(baseSize * 0.65)}px`,
            color: hudColor,
            fontWeight: 700,
            letterSpacing: "0.1em",
            opacity: 0.85,
          }}
        >
          [SYS//
        </span>

        {phraseWords.map((w, idx) => {
          const isSpoken = currentTime >= w.start;
          const isCurrentlyActive = currentTime >= w.start && currentTime <= w.end;

          const color = isCurrentlyActive
            ? "#FFFFFF"
            : isSpoken
            ? hudColor
            : "rgba(255, 255, 255, 0.75)";

          return (
            <span
              key={w.i ?? idx}
              style={{
                display: "inline-block",
                fontFamily: fonts.mono,
                fontSize: `${baseSize}px`,
                fontWeight: 800,
                textTransform: "uppercase",
                letterSpacing: "0.04em",
                lineHeight: 1.15,
                color,
                textShadow: isCurrentlyActive
                  ? `0 0 10px #FFFFFF, 0 0 20px ${hudColor}`
                  : `0 0 8px ${hudColor}66`,
                transform: isCurrentlyActive ? "scale(1.12)" : "scale(1)",
                transition: "all 0.08s ease",
              }}
            >
              {w.text}
            </span>
          );
        })}

        <span
          style={{
            fontFamily: fonts.mono,
            fontSize: `${Math.round(baseSize * 0.65)}px`,
            color: hudColor,
            fontWeight: 700,
            letterSpacing: "0.1em",
            opacity: 0.85,
          }}
        >
          ]
        </span>
      </div>
    </div>
  );
};
