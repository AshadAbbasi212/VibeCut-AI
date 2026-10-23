import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { getCaptionFontSize } from "../registry";

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

  // Caption size calculation (Default medium = 52px sweet spot)
  const baseSize = getCaptionFontSize(event.captionSize, 52);

  // Background style: "transparent" (default), "glass", "solid"
  const bgStyle = event.backgroundStyle || "transparent";
  const activeColor = event.highlightColor || "#38BDF8"; // Electric cyan default

  const containerBg =
    bgStyle === "solid"
      ? "rgba(255, 255, 255, 0.92)"
      : bgStyle === "glass"
      ? "rgba(10, 15, 25, 0.70)"
      : "transparent";

  const containerBorder =
    bgStyle === "glass"
      ? "1.5px solid rgba(255, 255, 255, 0.16)"
      : "none";

  const containerShadow =
    bgStyle === "solid"
      ? "0 8px 24px rgba(0, 0, 0, 0.22)"
      : bgStyle === "glass"
      ? "0 8px 32px rgba(0, 0, 0, 0.55)"
      : "none";

  const containerBackdrop =
    bgStyle === "glass" ? "blur(14px)" : undefined;

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        flexWrap: "wrap",
        gap: "10px",
        backgroundColor: containerBg,
        border: containerBorder,
        backdropFilter: containerBackdrop,
        WebkitBackdropFilter: containerBackdrop,
        padding: bgStyle === "transparent" ? "4px 8px" : "12px 28px",
        borderRadius: "9999px",
        boxShadow: containerShadow,
        transform: `scale(${scale})`,
        opacity,
        maxWidth: "92%",
        textAlign: "center",
      }}
    >
      {phraseWords.map((w, idx) => {
        const isSpoken = currentTime >= w.start;
        const highlight = event.highlights?.find((h) => h.wordIndex === w.i);

        let color: string;
        let textShadow: string;
        let fontWeight = 800;

        if (bgStyle === "solid") {
          color = isSpoken ? "#0F172A" : "#94A3B8";
          textShadow = "none";
        } else {
          // Transparent / Glass mode
          if (isSpoken) {
            color = highlight?.value || activeColor;
            fontWeight = 900;
            textShadow = `0 0 24px ${activeColor}99, 0 2px 10px rgba(0, 0, 0, 0.95), 0 0 4px rgba(0, 0, 0, 0.9)`;
          } else {
            color = "rgba(255, 255, 255, 0.88)";
            textShadow = "0 2px 8px rgba(0, 0, 0, 0.9), 0 0 3px rgba(0, 0, 0, 0.85)";
          }
        }

        return (
          <React.Fragment key={w.i ?? idx}>
            <span
              style={{
                fontFamily: fonts.sans,
                fontSize: `${baseSize}px`,
                fontWeight,
                lineHeight: 1.25,
                letterSpacing: "-0.01em",
                color,
                textShadow,
                WebkitTextStroke: bgStyle !== "solid" ? "1px rgba(0, 0, 0, 0.45)" : undefined,
                transition: "color 0.06s ease, transform 0.06s ease",
                transform: isSpoken && bgStyle !== "solid" ? "scale(1.05)" : "none",
                display: "inline-block",
                margin: "2px 6px",
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
