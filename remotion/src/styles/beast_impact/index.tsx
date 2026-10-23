import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { getCaptionFontSize } from "../registry";

interface BeastImpactProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const BeastImpact: React.FC<BeastImpactProps> = ({
  event,
  words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = event.start + frame / fps;
  const fonts = getFontFamilies();

  const scale = popIn(frame, fps, 0, 8, 0.4, 220);
  const opacity = fadeOut(frame, durationInFrames, 4);

  const [firstIdx, lastIdx] =
    event.wordRange && event.wordRange.length >= 2
      ? [event.wordRange[0], event.wordRange[1]]
      : [0, words.length - 1];

  const phraseWords = words.slice(firstIdx, lastIdx + 1);
  const baseSize = getCaptionFontSize(event.captionSize, 58);
  const activeColor = event.highlightColor || "#22C55E"; // Electric Lime for MrBeast Impact

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        flexWrap: "wrap",
        gap: "14px",
        transform: `scale(${scale}) rotate(-2deg)`,
        opacity,
        maxWidth: "94%",
        textAlign: "center",
        padding: "6px 12px",
      }}
    >
      {phraseWords.map((w, idx) => {
        const isSpoken = currentTime >= w.start;
        const isCurrentlyActive = currentTime >= w.start && currentTime <= w.end;

        const wordScale = isCurrentlyActive ? 1.22 : 1.0;
        const color = isCurrentlyActive ? "#FACC15" : isSpoken ? activeColor : "#FFFFFF";

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
                lineHeight: 1.1,
                color,
                WebkitTextStroke: isCurrentlyActive ? "5px #000000" : "3.5px #000000",
                paintOrder: "stroke fill",
                textShadow: isCurrentlyActive
                  ? `0 7px 0 #000000, 0 12px 24px rgba(0,0,0,0.9), 0 0 30px ${activeColor}`
                  : "0 4px 0 #000000, 0 6px 12px rgba(0,0,0,0.8)",
                transform: `scale(${wordScale})`,
                transition: "transform 0.06s cubic-bezier(0.34, 1.56, 0.64, 1)",
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
