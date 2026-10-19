import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { getCaptionFontSize } from "../registry";

interface TypewriterTerminalProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const TypewriterTerminal: React.FC<TypewriterTerminalProps> = ({
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

  // Blinking cursor: 0.5s period
  const cursorVisible = Math.floor((frame / fps) * 4) % 2 === 0;

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        flexWrap: "wrap",
        gap: "8px",
        backgroundColor: "rgba(15, 23, 42, 0.92)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        padding: "8px 22px",
        borderRadius: "10px",
        border: "1.5px solid #10B981",
        boxShadow: "0 8px 24px rgba(0, 0, 0, 0.5), 0 0 16px rgba(16, 185, 129, 0.3)",
        transform: `scale(${scale})`,
        opacity,
        maxWidth: "92%",
      }}
    >
      <span
        style={{
          fontFamily: fonts.mono,
          fontSize: `${getCaptionFontSize(event.captionSize, 42)}px`,
          fontWeight: 800,
          color: "#10B981",
          marginRight: "4px",
        }}
      >
        &gt;
      </span>

      {phraseWords.map((w, idx) => {
        const isSpoken = currentTime >= w.start;
        return (
          <span
            key={w.i ?? idx}
            style={{
              fontFamily: fonts.mono,
              fontSize: `${getCaptionFontSize(event.captionSize, 46)}px`,
              fontWeight: 700,
              color: isSpoken ? "#F8FAFC" : "#64748B",
              transition: "color 0.05s ease",
            }}
          >
            {w.text}
          </span>
        );
      })}

      <span
        style={{
          fontFamily: fonts.mono,
          fontSize: `${getCaptionFontSize(event.captionSize, 44)}px`,
          fontWeight: 900,
          color: "#10B981",
          opacity: cursorVisible ? 1 : 0,
          marginLeft: "2px",
        }}
      >
        _
      </span>
    </div>
  );
};
