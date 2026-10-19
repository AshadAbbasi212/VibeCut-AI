import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { getCaptionFontSize } from "../registry";

interface GlitchKineticProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const GlitchKinetic: React.FC<GlitchKineticProps> = ({
  event,
  words: _words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fonts = getFontFamilies();

  const scale = popIn(frame, fps, 0, 10, 0.4, 190);
  const opacity = fadeOut(frame, durationInFrames, 5);

  // Glitch jitter on initial entrance (first 8 frames)
  const isGlitching = frame < 8;
  const jitterX = isGlitching ? ((frame % 3) - 1) * 3 : 0;
  const jitterY = isGlitching ? (((frame + 1) % 3) - 1) * 2 : 0;

  return (
    <div
      style={{
        position: "relative",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        transform: `translate(${jitterX}px, ${jitterY}px) scale(${scale})`,
        opacity,
        padding: "8px 20px",
        backgroundColor: "rgba(0, 0, 0, 0.65)",
        backdropFilter: "blur(8px)",
        borderRadius: "8px",
        maxWidth: "92%",
        textAlign: "center",
      }}
    >
      {/* Cyan offset ghost */}
      <span
        style={{
          position: "absolute",
          top: "8px",
          left: `${20 - (isGlitching ? 3 : 1.5)}px`,
          right: `${20 + (isGlitching ? 3 : 1.5)}px`,
          fontFamily: fonts.sans,
          fontSize: `${getCaptionFontSize(event.captionSize, 52)}px`,
          fontWeight: 900,
          textTransform: "uppercase",
          letterSpacing: "0.02em",
          lineHeight: 1.2,
          color: "#00F0FF",
          opacity: 0.8,
          mixBlendMode: "screen",
          pointerEvents: "none",
        }}
      >
        {event.text}
      </span>

      {/* Magenta offset ghost */}
      <span
        style={{
          position: "absolute",
          top: "8px",
          left: `${20 + (isGlitching ? 3 : 1.5)}px`,
          right: `${20 - (isGlitching ? 3 : 1.5)}px`,
          fontFamily: fonts.sans,
          fontSize: `${getCaptionFontSize(event.captionSize, 52)}px`,
          fontWeight: 900,
          textTransform: "uppercase",
          letterSpacing: "0.02em",
          lineHeight: 1.2,
          color: "#FF0055",
          opacity: 0.8,
          mixBlendMode: "screen",
          pointerEvents: "none",
        }}
      >
        {event.text}
      </span>

      {/* Main crisp white text */}
      <span
        style={{
          position: "relative",
          fontFamily: fonts.sans,
          fontSize: `${getCaptionFontSize(event.captionSize, 52)}px`,
          fontWeight: 900,
          textTransform: "uppercase",
          letterSpacing: "0.02em",
          lineHeight: 1.2,
          color: "#FFFFFF",
          textShadow: "0 2px 10px rgba(0,0,0,0.8)",
        }}
      >
        {event.text}
      </span>
    </div>
  );
};
