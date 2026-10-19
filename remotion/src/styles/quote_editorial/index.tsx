import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { getCaptionFontSize } from "../registry";

interface QuoteEditorialProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const QuoteEditorial: React.FC<QuoteEditorialProps> = ({
  event,
  words: _words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fonts = getFontFamilies();

  const scale = popIn(frame, fps, 0, 12, 0.45, 170);
  const opacity = fadeOut(frame, durationInFrames, 6);

  return (
    <div
      style={{
        position: "relative",
        display: "inline-flex",
        flexDirection: "row",
        alignItems: "flex-start",
        justifyContent: "center",
        transform: `scale(${scale})`,
        opacity,
        padding: "10px 24px",
        backgroundColor: "rgba(17, 24, 39, 0.78)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        borderRadius: "16px",
        borderLeft: "3px solid #F59E0B",
        boxShadow: "0 10px 30px rgba(0, 0, 0, 0.4)",
        maxWidth: "92%",
      }}
    >
      <span
        style={{
          fontFamily: fonts.serif,
          fontSize: `${getCaptionFontSize(event.captionSize, 56)}px`,
          lineHeight: 0.8,
          color: "#F59E0B",
          marginRight: "10px",
          marginTop: "6px",
          fontStyle: "italic",
        }}
      >
        “
      </span>

      <span
        style={{
          fontFamily: fonts.serif,
          fontSize: `${getCaptionFontSize(event.captionSize, 48)}px`,
          fontStyle: "italic",
          fontWeight: 700,
          lineHeight: 1.25,
          color: "#FFFBEB",
          textShadow: "0 2px 8px rgba(0,0,0,0.5)",
        }}
      >
        {event.text}
      </span>
    </div>
  );
};
