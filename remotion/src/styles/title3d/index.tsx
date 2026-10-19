import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { Sparkles } from "../../decorations";

interface Title3dProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

const PALETTES: Record<string, string[][]> = {
  sunset: [
    ["#FDE047", "#FB923C"], // Yellow -> Peach/Orange
    ["#C084FC", "#67E8F9"], // Lavender -> Cyan
    ["#FDBA74", "#F43F5E"], // Peach -> Rose
  ],
  ocean: [
    ["#67E8F9", "#0284C7"], // Cyan -> Blue
    ["#A7F3D0", "#06B6D4"], // Mint -> Cyan
    ["#93C5FD", "#3B82F6"], // Sky -> Royal Blue
  ],
  candy: [
    ["#F472B6", "#A855F7"], // Pink -> Purple
    ["#FDE047", "#F43F5E"], // Yellow -> Pink
    ["#67E8F9", "#C084FC"], // Cyan -> Lavender
  ],
  mono: [
    ["#FFFFFF", "#D1D5DB"],
    ["#E5E7EB", "#9CA3AF"],
    ["#FFFFFF", "#E5E7EB"],
  ],
};

const make3dShadow = (color: string = "#1E1B4B", depth: number = 10): string => {
  const steps: string[] = [];
  for (let i = 1; i <= depth; i++) {
    steps.push(`${i}px ${i}px 0px ${color}`);
  }
  steps.push(`${depth + 2}px ${depth + 2}px 8px rgba(0, 0, 0, 0.6)`);
  return steps.join(", ");
};

export const Title3d: React.FC<Title3dProps> = ({
  event,
  words: _words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fonts = getFontFamilies();

  const scale = popIn(frame, fps, 0, 11, 0.5, 160);
  const opacity = fadeOut(frame, durationInFrames, 6);

  const paletteKey = event.palette || "sunset";
  const palette = PALETTES[paletteKey] || PALETTES.sunset;

  // Split lines: prefer event.lines if provided, otherwise group text into 2-3 lines
  const lines = event.lines && event.lines.length > 0
    ? event.lines
    : (() => {
        const words = event.text.split(" ");
        if (words.length <= 3) return [event.text];
        if (words.length <= 6) {
          const mid = Math.ceil(words.length / 2);
          return [words.slice(0, mid).join(" "), words.slice(mid).join(" ")];
        }
        const third = Math.ceil(words.length / 3);
        return [
          words.slice(0, third).join(" "),
          words.slice(third, third * 2).join(" "),
          words.slice(third * 2).join(" "),
        ];
      })();

  const shadow3d = make3dShadow("#1E1B4B", 5);

  return (
    <div
      style={{
        position: "relative",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        transform: `scale(${scale})`,
        opacity,
        textAlign: "center",
        maxWidth: "85%",
      }}
    >
      {/* Flanking sparkles */}
      <Sparkles
        size={26}
        color="#FDE047"
        phaseOffset={0}
        style={{
          position: "absolute",
          top: "40%",
          left: "-28px",
        }}
      />
      <Sparkles
        size={26}
        color="#FDE047"
        phaseOffset={Math.PI}
        style={{
          position: "absolute",
          top: "25%",
          right: "-28px",
        }}
      />

      {lines.map((lineText, idx) => {
        const [colorTop, colorBottom] = palette[idx % palette.length];
        const lineDelay = idx * 2; // subtle stagger
        const linePop = popIn(frame, fps, lineDelay, 12, 0.4, 200);

        return (
          <div
            key={idx}
            style={{
              position: "relative",
              margin: "-2px 0",
              transform: `scale(${linePop})`,
            }}
          >
            {/* Bottom 3D shadow layer with stroke */}
            <span
              style={{
                display: "block",
                fontFamily: fonts.condensed,
                fontSize: "44px",
                fontWeight: 900,
                textTransform: "uppercase",
                letterSpacing: "0.04em",
                lineHeight: 1.08,
                color: "#1E1B4B",
                textShadow: shadow3d,
                WebkitTextStroke: "3px #1E1B4B",
                paintOrder: "stroke fill",
              }}
            >
              {lineText}
            </span>

            {/* Top gradient fill layer */}
            <span
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                fontFamily: fonts.condensed,
                fontSize: "44px",
                fontWeight: 900,
                textTransform: "uppercase",
                letterSpacing: "0.04em",
                lineHeight: 1.08,
                background: `linear-gradient(180deg, ${colorTop} 15%, ${colorBottom} 85%)`,
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                filter: "drop-shadow(0 1px 1px rgba(255, 255, 255, 0.6))",
              }}
            >
              {lineText}
            </span>
          </div>
        );
      })}
    </div>
  );
};
