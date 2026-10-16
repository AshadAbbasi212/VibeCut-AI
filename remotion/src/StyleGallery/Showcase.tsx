import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { StyleGallery, SAMPLE_EVENTS } from "./index";

const STYLES_LIST = [
  "title3d",
  "blob_card",
  "blob_card_frosted",
  "pill_word",
  "serif_title",
  "numbered_point",
  "handwritten",
  "arc_letters",
  "sticker",
];

export const StyleShowcase: React.FC = () => {
  const framesPerStyle = 60; // 2 seconds at 30 fps

  return (
    <AbsoluteFill style={{ backgroundColor: "#09090B" }}>
      {STYLES_LIST.map((key, index) => {
        const from = index * framesPerStyle;
        const styleId = key === "blob_card_frosted" ? "blob_card" : key;
        const variant = key === "blob_card_frosted" ? "frosted" : undefined;

        return (
          <Sequence key={key} from={from} durationInFrames={framesPerStyle}>
            <StyleGallery styleId={styleId} variant={variant} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
