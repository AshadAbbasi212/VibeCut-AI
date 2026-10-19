import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";

interface MinimalUnderlineProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const MinimalUnderline: React.FC<MinimalUnderlineProps> = ({
  event,
  words: _words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fonts = getFontFamilies();

  const scale = popIn(frame, fps, 0, 11, 0.45, 170);
  const opacity = fadeOut(frame, durationInFrames, 5);

  // Smooth expanding underline progress
  const underlineProgress = Math.min(1, Math.max(0, frame / (fps * 0.4)));

  return (
    <div
      style={{
        position: "relative",
        display: "inline-flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        transform: `scale(${scale})`,
        opacity,
        padding: "6px 18px",
        backgroundColor: "rgba(0, 0, 0, 0.6)",
        backdropFilter: "blur(8px)",
        borderRadius: "8px",
        maxWidth: "85%",
        textAlign: "center",
      }}
    >
      <span
        style={{
          fontFamily: fonts.sans,
          fontSize: "34px",
          fontWeight: 800,
          lineHeight: 1.25,
          color: "#FFFFFF",
          textShadow: "0 2px 10px rgba(0, 0, 0, 0.7)",
          letterSpacing: "-0.01em",
        }}
      >
        {event.text}
      </span>

      {/* Dynamic Animated Gradient Underline Bar */}
      <div
        style={{
          marginTop: "6px",
          width: `${underlineProgress * 100}%`,
          height: "4px",
          borderRadius: "9999px",
          background: "linear-gradient(90deg, #F59E0B, #EF4444, #EC4899)",
          boxShadow: "0 0 10px rgba(245, 158, 11, 0.7)",
          transition: "width 0.1s ease-out",
        }}
      />
    </div>
  );
};
