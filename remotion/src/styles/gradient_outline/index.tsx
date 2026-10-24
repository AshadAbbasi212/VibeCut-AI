import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { getCaptionFontSize } from "../registry";

interface GradientOutlineProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const GradientOutline: React.FC<GradientOutlineProps> = ({
  event,
  words: _words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fonts = getFontFamilies();

  const springScale = popIn(frame, fps, 0, 11, 0.45, 170);
  // Ensure entrance scale never drops below 0.75 so text is never a microscopic dot
  const scale = Math.max(0.75, springScale);
  const opacity = fadeOut(frame, durationInFrames, 5);

  return (
    <div
      style={{
        position: "relative",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        transform: `scale(${scale})`,
        opacity,
        padding: "12px 28px",
        borderRadius: "20px",
        minWidth: "220px",
        boxSizing: "border-box",
        background: "rgba(15, 23, 42, 0.85)",
        backdropFilter: "blur(14px)",
        WebkitBackdropFilter: "blur(14px)",
        boxShadow: "0 10px 32px rgba(0, 0, 0, 0.45)",
        border: "2.5px solid transparent",
        backgroundImage:
          "linear-gradient(rgba(15, 23, 42, 0.88), rgba(15, 23, 42, 0.88)), linear-gradient(135deg, #EC4899, #8B5CF6, #3B82F6)",
        backgroundOrigin: "border-box",
        backgroundClip: "padding-box, border-box",
        maxWidth: "90%",
        textAlign: "center",
      }}
    >
      <span
        style={{
          fontFamily: fonts.sans,
          fontSize: `${getCaptionFontSize(event.captionSize, 48)}px`,
          fontWeight: 900,
          textTransform: "uppercase",
          letterSpacing: "0.03em",
          lineHeight: 1.25,
          background: "linear-gradient(135deg, #F472B6, #C084FC, #60A5FA)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          filter: "drop-shadow(0 2px 8px rgba(139, 92, 246, 0.35))",
        }}
      >
        {event.text}
      </span>
    </div>
  );
};
