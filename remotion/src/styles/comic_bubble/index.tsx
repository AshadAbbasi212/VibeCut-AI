import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { getCaptionFontSize } from "../registry";

interface ComicBubbleProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const ComicBubble: React.FC<ComicBubbleProps> = ({
  event,
  words: _words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fonts = getFontFamilies();

  const scale = popIn(frame, fps, 0, 11, 0.45, 180);
  const opacity = fadeOut(frame, durationInFrames, 5);

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
        backgroundColor: "#FFFFFF",
        padding: "10px 24px",
        borderRadius: "20px",
        border: "3px solid #000000",
        boxShadow: "4px 4px 0px #000000",
        maxWidth: "92%",
        textAlign: "center",
      }}
    >
      <span
        style={{
          fontFamily: fonts.sans,
          fontSize: `${getCaptionFontSize(event.captionSize, 48)}px`,
          fontWeight: 900,
          textTransform: "uppercase",
          letterSpacing: "0.02em",
          lineHeight: 1.2,
          color: "#000000",
        }}
      >
        {event.text}
      </span>

      {/* Comic speech bubble tail notch */}
      <div
        style={{
          position: "absolute",
          bottom: "-12px",
          left: "30px",
          width: 0,
          height: 0,
          borderLeft: "10px solid transparent",
          borderRight: "4px solid transparent",
          borderTop: "12px solid #000000",
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: "-9px",
          left: "32px",
          width: 0,
          height: 0,
          borderLeft: "7px solid transparent",
          borderRight: "3px solid transparent",
          borderTop: "9px solid #FFFFFF",
        }}
      />
    </div>
  );
};
