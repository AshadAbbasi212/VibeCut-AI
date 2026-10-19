import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";

interface HandwrittenProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const Handwritten: React.FC<HandwrittenProps> = ({
  event,
  words: _words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fonts = getFontFamilies();

  const scale = popIn(frame, fps, 0, 14, 0.5, 160);
  const opacity = fadeOut(frame, durationInFrames, 5);

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        transform: `scale(${scale})`,
        opacity,
        padding: "6px 18px",
        textAlign: "center",
      }}
    >
      <span
        style={{
          fontFamily: fonts.handwriting,
          fontSize: "30px",
          fontWeight: 700,
          lineHeight: 1.2,
          color: "#FFFFFF",
          textShadow: "0 2px 8px rgba(0, 0, 0, 0.7), 0 0 2px rgba(0, 0, 0, 0.9)",
          letterSpacing: "0.02em",
        }}
      >
        {event.text}
      </span>
    </div>
  );
};
