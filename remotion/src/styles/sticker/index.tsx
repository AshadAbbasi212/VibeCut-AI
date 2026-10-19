import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { TimelineEvent, TimelineWord } from "../../types/timeline";
import { popIn, fadeOut, floatY } from "../../anim";
import { getFontFamilies } from "../../load-font";
import { GraphicRenderer } from "../../decorations";
import { getCaptionFontSize } from "../registry";

interface StickerProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const Sticker: React.FC<StickerProps> = ({
  event,
  words: _words,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fonts = getFontFamilies();

  const scale = popIn(frame, fps, 0, 10, 0.45, 180);
  const opacity = fadeOut(frame, durationInFrames, 6);
  const floatOffset = floatY(frame, fps, 7, 1.4);

  // Determine graphic data
  const graphic = event.graphic || {
    kind: "emoji",
    value: event.text || "💡",
  };

  return (
    <div
      style={{
        display: "inline-flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        transform: `translateY(${floatOffset}px) scale(${scale})`,
        opacity,
        textAlign: "center",
      }}
    >
      {/* Sticker icon / emoji / image via GraphicRenderer */}
      <GraphicRenderer
        graphic={graphic}
        size={60}
        glowColor="rgba(56, 189, 248, 0.85)"
      />

      {/* Optional accompanying text tag */}
      {event.text && event.text !== graphic.value && (
        <span
          style={{
            marginTop: "8px",
            fontFamily: fonts.sans,
            fontSize: `${getCaptionFontSize(event.captionSize, 40)}px`,
            fontWeight: 800,
            color: "#FFFFFF",
            backgroundColor: "rgba(15, 23, 42, 0.75)",
            backdropFilter: "blur(8px)",
            padding: "4px 14px",
            borderRadius: "9999px",
            border: "1px solid rgba(56, 189, 248, 0.5)",
            textShadow: "0 2px 4px rgba(0,0,0,0.5)",
          }}
        >
          {event.text}
        </span>
      )}
    </div>
  );
};
