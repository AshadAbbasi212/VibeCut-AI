import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";

interface PillWordProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const PillWord: React.FC<PillWordProps> = ({
  event,
  words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = event.start + frame / fps;
  const fonts = getFontFamilies();

  const scale = popIn(frame, fps, 0, 14, 0.6, 180);
  const opacity = fadeOut(frame, durationInFrames, 5);

  // Extract words for this event
  const [firstIdx, lastIdx] =
    event.wordRange && event.wordRange.length >= 2
      ? [event.wordRange[0], event.wordRange[1]]
      : [0, words.length - 1];

  const phraseWords = words.slice(firstIdx, lastIdx + 1);

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        flexWrap: "nowrap",
        gap: "8px",
        backgroundColor: "rgba(255, 255, 255, 0.90)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        padding: "10px 24px",
        borderRadius: "9999px",
        boxShadow: "0 8px 24px rgba(0, 0, 0, 0.18), 0 2px 6px rgba(0, 0, 0, 0.08)",
        transform: `scale(${scale})`,
        opacity,
        maxWidth: "85%",
      }}
    >
      {phraseWords.map((w, idx) => {
        const isSpoken = currentTime >= w.start;
        // Check for specific highlight overrides on this word index
        const highlight = event.highlights?.find(
          (h) => h.wordIndex === w.i
        );

        let color = isSpoken ? "#111827" : "#9ca3af";
        let background = "transparent";
        let padding = "0px";
        let borderRadius = "0px";

        if (highlight) {
          if (highlight.kind === "color" && isSpoken) {
            color = highlight.value;
          } else if (highlight.kind === "pill") {
            background = highlight.value;
            color = "#dc2626"; // Crimson
            padding = "2px 8px";
            borderRadius = "6px";
          }
        }

        return (
          <span
            key={w.i ?? idx}
            style={{
              fontFamily: fonts.sans,
              fontSize: "32px",
              fontWeight: 800,
              lineHeight: 1.2,
              letterSpacing: "-0.01em",
              color,
              backgroundColor: background,
              padding,
              borderRadius,
              transition: "color 0.05s ease",
            }}
          >
            {w.text}
          </span>
        );
      })}
    </div>
  );
};
