import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { getCaptionFontSize } from "../registry";

interface NeonGlowProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const NeonGlow: React.FC<NeonGlowProps> = ({
  event,
  words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = event.start + frame / fps;
  const fonts = getFontFamilies();

  const scale = popIn(frame, fps, 0, 12, 0.5, 170);
  const opacity = fadeOut(frame, durationInFrames, 5);

  const [firstIdx, lastIdx] =
    event.wordRange && event.wordRange.length >= 2
      ? [event.wordRange[0], event.wordRange[1]]
      : [0, words.length - 1];

  const phraseWords = words.slice(firstIdx, lastIdx + 1);

  // Subtle pulsating neon glow
  const t = (frame / fps) * 2 * Math.PI;
  const pulse = 0.85 + Math.sin(t * 3) * 0.15;

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        flexWrap: "wrap",
        gap: "10px",
        backgroundColor: "rgba(10, 15, 29, 0.82)",
        backdropFilter: "blur(14px)",
        WebkitBackdropFilter: "blur(14px)",
        padding: "10px 26px",
        borderRadius: "9999px",
        border: `1.5px solid rgba(6, 182, 212, ${pulse * 0.9})`,
        boxShadow: `0 0 20px rgba(6, 182, 212, ${pulse * 0.4}), inset 0 0 10px rgba(6, 182, 212, 0.2)`,
        transform: `scale(${scale})`,
        opacity,
        maxWidth: "92%",
        textAlign: "center",
      }}
    >
      {phraseWords.map((w, idx) => {
        const isSpoken = currentTime >= w.start;
        return (
          <React.Fragment key={w.i ?? idx}>
            <span
              style={{
                display: "inline-block",
                margin: "2px 6px",
                fontFamily: fonts.sans,
                fontSize: `${getCaptionFontSize(event.captionSize, 52)}px`,
                fontWeight: 900,
                textTransform: "uppercase",
                letterSpacing: "0.04em",
                lineHeight: 1.2,
                color: isSpoken ? "#22D3EE" : "rgba(226, 232, 240, 0.45)",
                textShadow: isSpoken
                  ? `0 0 10px #06B6D4, 0 0 22px #06B6D4, 0 0 35px #3B82F6`
                  : "none",
                transition: "color 0.05s ease, text-shadow 0.05s ease",
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
