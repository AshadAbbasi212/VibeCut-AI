import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut, floatY } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { getCaptionFontSize } from "../registry";

interface ArcLettersProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

const PASTEL_COLORS = [
  "#FB923C", // Orange/peach
  "#FDE047", // Yellow
  "#86EFAC", // Mint
  "#38BDF8", // Cyan/aqua
  "#C084FC", // Lavender
  "#F472B6", // Pink
];

export const ArcLetters: React.FC<ArcLettersProps> = ({
  event,
  words: _words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fonts = getFontFamilies();

  const scale = popIn(frame, fps, 0, 11, 0.45, 170);
  const opacity = fadeOut(frame, durationInFrames, 6);
  const floatOffset = floatY(frame, fps, 8, 1.2);

  // Split into tokens or characters
  const rawTokens = event.text.includes(" ")
    ? event.text.split(" ")
    : event.text.split("");
  const tokens = rawTokens.filter((t) => t.trim().length > 0);

  const total = tokens.length;
  // Arc parameters: distribute angle from -25 deg to +25 deg
  const maxAngle = Math.min(35, total * 10);
  const radius = 120;

  return (
    <div
      style={{
        position: "relative",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        transform: `translateY(${floatOffset}px) scale(${scale})`,
        opacity,
        height: "90px",
      }}
    >
      {tokens.map((token, idx) => {
        const color = PASTEL_COLORS[idx % PASTEL_COLORS.length];
        const angleDeg =
          total > 1
            ? -maxAngle + (idx / (total - 1)) * (maxAngle * 2)
            : 0;
        const angleRad = (angleDeg * Math.PI) / 180;
        const x = Math.sin(angleRad) * radius;
        const y = -Math.cos(angleRad) * radius + radius;

        const tokenPop = popIn(frame, fps, idx * 2, 12, 0.4, 200);

        return (
          <span
            key={idx}
            style={{
              position: "absolute",
              left: "50%",
              top: "50%",
              transform: `translate(-50%, -50%) translate(${x}px, ${y}px) rotate(${angleDeg}deg) scale(${tokenPop})`,
              fontFamily: fonts.sans,
              fontSize: `${getCaptionFontSize(event.captionSize, 52)}px`,
              fontWeight: 900,
              color,
              textShadow: `0 0 16px ${color}AA, 0 3px 8px rgba(0,0,0,0.6)`,
              WebkitTextStroke: "1.5px rgba(255, 255, 255, 0.7)",
              lineHeight: 1,
            }}
          >
            {token}
          </span>
        );
      })}
    </div>
  );
};
