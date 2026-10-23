import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { getCaptionFontSize } from "../registry";

interface KaraokeBounceProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const KaraokeBounce: React.FC<KaraokeBounceProps> = ({
  event,
  words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = event.start + frame / fps;
  const fonts = getFontFamilies();

  const scale = popIn(frame, fps, 0, 11, 0.45, 175);
  const opacity = fadeOut(frame, durationInFrames, 5);

  const [firstIdx, lastIdx] =
    event.wordRange && event.wordRange.length >= 2
      ? [event.wordRange[0], event.wordRange[1]]
      : [0, words.length - 1];

  const phraseWords = words.slice(firstIdx, lastIdx + 1);
  const baseSize = getCaptionFontSize(event.captionSize, 52);
  const activeColor = event.highlightColor || "#FBBF24"; // Cyber gold default

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        flexWrap: "wrap",
        gap: "10px",
        backgroundColor: "rgba(10, 15, 29, 0.75)",
        backdropFilter: "blur(10px)",
        padding: "10px 24px",
        borderRadius: "9999px",
        boxShadow: "0 8px 24px rgba(0, 0, 0, 0.4)",
        transform: `scale(${scale})`,
        opacity,
        maxWidth: "92%",
        textAlign: "center",
      }}
    >
      {phraseWords.map((w, idx) => {
        const isSpoken = currentTime >= w.start;
        const isCurrentlyActive = currentTime >= w.start && currentTime <= w.end;

        // Bouncing dot height calculation (parabola during word duration)
        let bounceY = 0;
        if (isCurrentlyActive && w.end > w.start) {
          const progress = (currentTime - w.start) / (w.end - w.start);
          bounceY = -Math.sin(progress * Math.PI) * 16;
        }

        return (
          <React.Fragment key={w.i ?? idx}>
            <span
              style={{
                position: "relative",
                display: "inline-block",
                margin: "2px 6px",
                fontFamily: fonts.sans,
                fontSize: `${baseSize}px`,
                fontWeight: 800,
                lineHeight: 1.2,
                color: isSpoken ? activeColor : "#FFFFFF",
                textShadow: isSpoken
                  ? `0 0 12px ${activeColor}AA, 0 2px 8px rgba(0, 0, 0, 0.9)`
                  : "0 2px 6px rgba(0, 0, 0, 0.8)",
                transition: "color 0.06s ease",
              }}
            >
              {/* Bouncing ball indicator over active spoken word */}
              {isCurrentlyActive && (
                <span
                  style={{
                    position: "absolute",
                    top: "-14px",
                    left: "50%",
                    transform: `translateX(-50%) translateY(${bounceY}px)`,
                    width: "10px",
                    height: "10px",
                    borderRadius: "50%",
                    backgroundColor: activeColor,
                    boxShadow: `0 0 10px ${activeColor}, 0 2px 4px rgba(0,0,0,0.6)`,
                    pointerEvents: "none",
                  }}
                />
              )}
              {w.text}
            </span>
            {idx < phraseWords.length - 1 && " "}
          </React.Fragment>
        );
      })}
    </div>
  );
};
