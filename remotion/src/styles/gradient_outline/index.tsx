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

  const scale = popIn(frame, fps, 0, 11, 0.45, 170);
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
        padding: "8px 24px",
        borderRadius: "9999px",
        background: "rgba(15, 23, 42, 0.82)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        boxShadow: "0 8px 30px rgba(0, 0, 0, 0.35)",
        border: "2px solid transparent",
        backgroundImage:
          "linear-gradient(rgba(15, 23, 42, 0.85), rgba(15, 23, 42, 0.85)), linear-gradient(135deg, #EC4899, #8B5CF6, #3B82F6)",
        backgroundOrigin: "border-box",
        backgroundClip: "padding-box, border-box",
        maxWidth: "92%",
        textAlign: "center",
      }}
    >
      <span
        style={{
          fontFamily: fonts.sans,
          fontSize: `${getCaptionFontSize(event.captionSize, 50)}px`,
          fontWeight: 900,
          textTransform: "uppercase",
          letterSpacing: "0.03em",
          lineHeight: 1.2,
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
