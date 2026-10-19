import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { getCaptionFontSize } from "../registry";

interface RetroVaporwaveProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const RetroVaporwave: React.FC<RetroVaporwaveProps> = ({
  event,
  words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = event.start + frame / fps;
  const fonts = getFontFamilies();

  const scale = popIn(frame, fps, 0, 11, 0.45, 175);
  const opacity = fadeOut(frame, durationInFrames, 5);

  const [firstIdx, lastIdx] =
    event.wordRange && event.wordRange.length >= 2
      ? [event.wordRange[0], event.wordRange[1]]
      : [0, words.length - 1];

  const phraseWords = words.slice(firstIdx, lastIdx + 1);
  const baseSize = getCaptionFontSize(event.captionSize, 52);

  // Subtle 80s synth pulse
  const t = (frame / fps) * 2 * Math.PI;
  const pulse = 0.88 + Math.sin(t * 2.5) * 0.12;

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        flexWrap: "wrap",
        gap: "10px",
        background: "rgba(15, 7, 32, 0.85)",
        backdropFilter: "blur(14px)",
        WebkitBackdropFilter: "blur(14px)",
        padding: "10px 24px",
        borderRadius: "14px",
        border: `2px solid rgba(244, 63, 94, ${pulse})`,
        boxShadow: `0 0 20px rgba(244, 63, 94, ${pulse * 0.5}), inset 0 0 15px rgba(6, 182, 212, 0.3)`,
        transform: `scale(${scale})`,
        opacity,
        maxWidth: "92%",
        textAlign: "center",
      }}
    >
      {phraseWords.map((w, idx) => {
        const isSpoken = currentTime >= w.start;

        return (
          <span
            key={w.i ?? idx}
            style={{
              fontFamily: fonts.condensed,
              fontSize: `${baseSize}px`,
              fontWeight: 900,
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              lineHeight: 1.15,
              background: isSpoken
                ? "linear-gradient(180deg, #F43F5E 0%, #FB7185 45%, #38BDF8 100%)"
                : "linear-gradient(180deg, #94A3B8 0%, #64748B 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              filter: isSpoken
                ? "drop-shadow(0 0 8px rgba(244, 63, 94, 0.8)) drop-shadow(0 0 14px rgba(56, 189, 248, 0.6))"
                : "none",
              transition: "filter 0.08s ease",
            }}
          >
            {w.text}
          </span>
        );
      })}
    </div>
  );
};
