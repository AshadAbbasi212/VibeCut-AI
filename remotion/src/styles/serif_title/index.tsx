import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { EllipseDoodle } from "../../decorations";
import { getCaptionFontSize } from "../registry";

interface SerifTitleProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const SerifTitle: React.FC<SerifTitleProps> = ({
  event,
  words: _words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fonts = getFontFamilies();

  const scale = popIn(frame, fps, 0, 12, 0.5, 170);
  const opacity = fadeOut(frame, durationInFrames, 6);

  // Ellipse stroke progress
  const ellipseProgress = Math.min(1, Math.max(0, (frame - 6) / (fps * 0.45)));

  // Use pre-split lines if available or intelligent grouping
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
        transform: `scale(${scale})`,
        opacity,
        textAlign: "center",
        padding: "16px 32px",
      }}
    >
      {/* Tilted Hand-drawn Ellipse Doodle */}
      <EllipseDoodle
        width={340}
        height={130}
        strokeColor="#FFFFFF"
        strokeWidth={2.5}
        progress={ellipseProgress}
        style={{
          top: "48%",
          left: "50%",
          transform: "translate(-50%, -50%) rotate(-7deg)",
        }}
      />

      {lines.map((lineText, idx) => {
        // Parse words and group consecutive pill tokens (e.g. STOP PLANNING)
        const wordsInLine = lineText.split(" ");
        const tokens: { text: string; kind: "normal" | "pill" | "yellow" }[] = [];

        for (const word of wordsInLine) {
          const cleanUpper = word.replace(/[^a-zA-Z]/g, "").toUpperCase();
          const isPill =
            cleanUpper === "STOP" ||
            cleanUpper === "PLANNING" ||
            (event.highlights &&
              event.highlights.some(
                (h) => h.kind === "pill" && word.toLowerCase().includes(h.value.toLowerCase())
              ));
          const isYellow =
            cleanUpper === "TAKE" ||
            cleanUpper === "ACTION" ||
            cleanUpper === "MONETISE" ||
            (event.highlights &&
              event.highlights.some(
                (h) => h.kind === "color" && word.toLowerCase().includes(h.value.toLowerCase())
              ));

          const kind = isPill ? "pill" : isYellow ? "yellow" : "normal";

          // If previous token was pill and this is pill, combine them!
          if (kind === "pill" && tokens.length > 0 && tokens[tokens.length - 1].kind === "pill") {
            tokens[tokens.length - 1].text += " " + word;
          } else {
            tokens.push({ text: word, kind });
          }
        }

        return (
          <div
            key={idx}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "10px",
              margin: "3px 0",
              fontFamily: fonts.serif,
              fontSize: `${getCaptionFontSize(event.captionSize, 52)}px`,
              fontWeight: 800,
              lineHeight: 1.2,
              color: "#FFFFFF",
              textShadow: "0 3px 12px rgba(0, 0, 0, 0.6), 0 1px 3px rgba(0, 0, 0, 0.8)",
              letterSpacing: "-0.01em",
            }}
          >
            {tokens.map((token, tIdx) => {
              if (token.kind === "pill") {
                return (
                  <span
                    key={tIdx}
                    style={{
                      backgroundColor: "#FFFFFF",
                      color: "#E11D48",
                      padding: "2px 14px",
                      borderRadius: "9999px",
                      fontWeight: 900,
                      textTransform: "uppercase",
                      boxShadow: "0 3px 10px rgba(0, 0, 0, 0.25)",
                      textShadow: "none",
                      display: "inline-block",
                      letterSpacing: "0.02em",
                    }}
                  >
                    {token.text}
                  </span>
                );
              }

              if (token.kind === "yellow") {
                return (
                  <span
                    key={tIdx}
                    style={{
                      color: "#FBBF24",
                      fontWeight: 900,
                      textTransform: "uppercase",
                      display: "inline-block",
                    }}
                  >
                    {token.text}
                  </span>
                );
              }

              return (
                <span key={tIdx} style={{ display: "inline-block" }}>
                  {token.text}
                </span>
              );
            })}
          </div>
        );
      })}
    </div>
  );
};
