import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { Sparkles } from "../../decorations";

interface BlobCardProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const BlobCard: React.FC<BlobCardProps> = ({
  event,
  words: _words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fonts = getFontFamilies();

  const scale = popIn(frame, fps, 0, 12, 0.6, 170);
  const opacity = fadeOut(frame, durationInFrames, 6);

  // Subtle breathing oscillation
  const t = (frame / fps) * 2 * Math.PI;
  const breatheScale = 1 + Math.sin(t * 0.8) * 0.015;

  const isFrosted = event.variant === "frosted";

  // Lines of text
  const lines = event.lines && event.lines.length > 0
    ? event.lines
    : (() => {
        const words = event.text.split(" ");
        if (words.length <= 4) return [event.text];
        const mid = Math.ceil(words.length / 2);
        return [words.slice(0, mid).join(" "), words.slice(mid).join(" ")];
      })();

  return (
    <div
      style={{
        position: "relative",
        display: "inline-flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        transform: `scale(${scale * breatheScale})`,
        opacity,
        padding: "16px 36px",
        borderRadius: "58% 42% 52% 48% / 44% 56% 44% 56%",
        background: isFrosted
          ? "radial-gradient(ellipse at center, rgba(255, 255, 255, 0.42) 0%, rgba(240, 243, 246, 0.28) 100%)"
          : "radial-gradient(ellipse at center, #312E81 0%, #1E1B4B 65%, #0F172A 100%)",
        backdropFilter: isFrosted ? "blur(18px)" : "blur(12px)",
        WebkitBackdropFilter: isFrosted ? "blur(18px)" : "blur(12px)",
        boxShadow: isFrosted
          ? "0 12px 30px rgba(0, 0, 0, 0.15), inset 0 1px 2px rgba(255, 255, 255, 0.6)"
          : "0 14px 36px rgba(30, 27, 75, 0.5), 0 0 20px rgba(99, 102, 241, 0.35)",
        border: isFrosted
          ? "1.5px solid rgba(255, 255, 255, 0.5)"
          : "1.5px solid rgba(165, 180, 252, 0.25)",
        maxWidth: "80%",
        textAlign: "center",
      }}
    >
      {/* Decorative Sparkles for glow variant */}
      {!isFrosted && (
        <>
          <Sparkles
            size={22}
            color="#FDE047"
            phaseOffset={0}
            style={{
              position: "absolute",
              top: "12%",
              left: "-12px",
            }}
          />
          <Sparkles
            size={22}
            color="#FDE047"
            phaseOffset={Math.PI * 0.7}
            style={{
              position: "absolute",
              bottom: "12%",
              right: "-12px",
            }}
          />
        </>
      )}

      {lines.map((line, idx) => {
        // Highlight words if red emphasis is requested
        const wordsInLine = line.split(" ");
        return (
          <div
            key={idx}
            style={{
              fontFamily: fonts.serif,
              fontSize: "32px",
              fontWeight: 700,
              lineHeight: 1.25,
              color: isFrosted ? "#FFFFFF" : "#FFFFFF",
              textShadow: isFrosted
                ? "0 2px 8px rgba(0, 0, 0, 0.45)"
                : "0 2px 10px rgba(0, 0, 0, 0.5)",
              margin: "2px 0",
              letterSpacing: "-0.01em",
            }}
          >
            {wordsInLine.map((word, wIdx) => {
              const cleanWord = word.replace(/[^a-zA-Z]/g, "").toUpperCase();
              const isRedEmphasis =
                isFrosted &&
                (cleanWord === "NOT" ||
                  cleanWord === "NEVER" ||
                  word.toLowerCase().includes("advice"));

              return (
                <span
                  key={wIdx}
                  style={{
                    color: isRedEmphasis ? "#E11D48" : "inherit",
                    fontWeight: isRedEmphasis ? 900 : 700,
                    marginRight: wIdx < wordsInLine.length - 1 ? "10px" : "0",
                  }}
                >
                  {word}
                </span>
              );
            })}
          </div>
        );
      })}
    </div>
  );
};
