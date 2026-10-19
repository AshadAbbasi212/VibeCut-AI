import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { getCaptionFontSize } from "../registry";

interface PaperCutoutProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const PaperCutout: React.FC<PaperCutoutProps> = ({
  event,
  words: _words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fonts = getFontFamilies();

  const scale = popIn(frame, fps, 0, 12, 0.45, 170);
  const opacity = fadeOut(frame, durationInFrames, 5);

  // Subtle pseudo-random tilt based on event id length
  const tilt = (event.id.length % 2 === 0 ? -2.2 : 2.5);

  return (
    <div
      style={{
        position: "relative",
        display: "inline-flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        transform: `rotate(${tilt}deg) scale(${scale})`,
        opacity,
        backgroundColor: "#FEF08A", // warm sticky paper
        color: "#0F172A",
        padding: "10px 24px",
        borderRadius: "3px",
        boxShadow: "0 8px 24px rgba(0, 0, 0, 0.35), 0 2px 4px rgba(0,0,0,0.2)",
        maxWidth: "92%",
        textAlign: "center",
      }}
    >
      {/* Translucent washi tape at top */}
      <div
        style={{
          position: "absolute",
          top: "-10px",
          width: "48px",
          height: "18px",
          backgroundColor: "rgba(244, 63, 94, 0.45)",
          backdropFilter: "blur(4px)",
          transform: "rotate(-3deg)",
          borderRadius: "1px",
        }}
      />

      <span
        style={{
          fontFamily: fonts.sans,
          fontSize: `${getCaptionFontSize(event.captionSize, 48)}px`,
          fontWeight: 800,
          lineHeight: 1.25,
          letterSpacing: "-0.01em",
          color: "#0F172A",
        }}
      >
        {event.text}
      </span>
    </div>
  );
};
