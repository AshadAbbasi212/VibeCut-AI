import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { EllipseDoodle } from "../../decorations";

interface NumberedPointProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const NumberedPoint: React.FC<NumberedPointProps> = ({
  event,
  words: _words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fonts = getFontFamilies();

  const scale = popIn(frame, fps, 0, 12, 0.5, 170);
  const opacity = fadeOut(frame, durationInFrames, 6);

  // Extract numeral if present in text e.g. "Number one" or "1." or default "1"
  const match = event.text.match(/\b(1|2|3|4|5|one|two|three|four|five|first|second|third)\b/i);
  let numeral = "1";
  if (match) {
    const val = match[1].toLowerCase();
    if (val === "one" || val === "first" || val === "1") numeral = "1";
    else if (val === "two" || val === "second" || val === "2") numeral = "2";
    else if (val === "three" || val === "third" || val === "3") numeral = "3";
    else if (val === "four" || val === "4") numeral = "4";
    else if (val === "five" || val === "5") numeral = "5";
  }

  const ellipseProgress = Math.min(1, Math.max(0, (frame - 4) / (fps * 0.4)));

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
        transform: `scale(${scale})`,
        opacity,
        textAlign: "center",
      }}
    >
      {/* Circled Italic Numeral */}
      <div
        style={{
          position: "relative",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          width: "56px",
          height: "56px",
          marginBottom: "8px",
        }}
      >
        <span
          style={{
            fontFamily: fonts.serif,
            fontStyle: "italic",
            fontSize: "38px",
            fontWeight: 800,
            color: "#FFFFFF",
            textShadow: "0 2px 8px rgba(0,0,0,0.5)",
          }}
        >
          {numeral}
        </span>
        <EllipseDoodle
          width={64}
          height={52}
          strokeColor="#FFFFFF"
          strokeWidth={2.5}
          progress={ellipseProgress}
          style={{
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%) rotate(-12deg)",
          }}
        />
      </div>

      {/* Spoken claim lines */}
      {lines.map((lineText, idx) => {
        const wordsInLine = lineText.split(" ");
        return (
          <div
            key={idx}
            style={{
              fontFamily: fonts.serif,
              fontSize: "32px",
              fontWeight: 700,
              lineHeight: 1.25,
              color: "#FFFFFF",
              textShadow: "0 3px 12px rgba(0, 0, 0, 0.6)",
              margin: "2px 0",
              letterSpacing: "-0.01em",
            }}
          >
            {wordsInLine.map((word, wIdx) => {
              const clean = word.toLowerCase().replace(/[^a-z]/g, "");
              const isYellowItalic =
                clean === "monetise" ||
                clean === "monetize" ||
                clean === "skills" ||
                clean === "action" ||
                (event.highlights &&
                  event.highlights.some(
                    (h) => h.kind === "color" && word.toLowerCase().includes(h.value.toLowerCase())
                  ));

              return (
                <span
                  key={wIdx}
                  style={{
                    color: isYellowItalic ? "#FBBF24" : "inherit",
                    fontStyle: isYellowItalic ? "italic" : "normal",
                    fontWeight: isYellowItalic ? 800 : 700,
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
