import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { getCaptionFontSize } from "../registry";

interface HormoziBoldProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const HormoziBold: React.FC<HormoziBoldProps> = ({
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
  const baseSize = getCaptionFontSize(event.captionSize, 54);
  const activeColor = event.highlightColor || "#FDE047"; // Electric yellow default for Hormozi

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        flexWrap: "wrap",
        gap: "10px 18px",
        transform: `scale(${scale})`,
        opacity,
        maxWidth: "92%",
        textAlign: "center",
        padding: "4px 8px",
      }}
    >
      {phraseWords.map((w, idx) => {
        const isSpoken = currentTime >= w.start;
        const isCurrentlyActive = currentTime >= w.start && currentTime <= w.end;

        const wordScale = isCurrentlyActive ? 1.14 : 1.0;
        const color = isSpoken ? activeColor : "#FFFFFF";
        const strokeColor = "#000000";

        return (
          <React.Fragment key={w.i ?? idx}>
            <span
              style={{
                display: "inline-block",
                margin: "4px 8px",
                fontFamily: fonts.sans,
                fontSize: `${baseSize}px`,
                fontWeight: 900,
                textTransform: "uppercase",
                letterSpacing: "0.04em",
                lineHeight: 1.15,
                color,
                WebkitTextStroke: isCurrentlyActive ? `4px ${strokeColor}` : `3px ${strokeColor}`,
                paintOrder: "stroke fill",
                textShadow: isCurrentlyActive
                  ? `0 5px 0 #000000, 0 8px 16px rgba(0, 0, 0, 0.8), 0 0 20px ${activeColor}88`
                  : "0 3px 0 #000000, 0 5px 10px rgba(0, 0, 0, 0.7)",
                transform: `scale(${wordScale})`,
                transition: "transform 0.08s cubic-bezier(0.34, 1.56, 0.64, 1), color 0.05s ease",
              }}
            >
              {w.text}
            </span>
            {idx < phraseWords.length - 1 && " "}
          </React.Fragment>
        );
      })}
    </div>
  );
};
