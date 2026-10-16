import React from "react";
import { TimelineEvent, TimelineWord } from "../types/timeline";
import { PillWord } from "./pill_word";
import { Title3d } from "./title3d";
import { BlobCard } from "./blob_card";
import { SerifTitle } from "./serif_title";
import { NumberedPoint } from "./numbered_point";
import { Handwritten } from "./handwritten";
import { ArcLetters } from "./arc_letters";
import { Sticker } from "./sticker";

export interface StyleComponentProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const STYLE_REGISTRY: Record<string, React.FC<StyleComponentProps>> = {
  pill_word: PillWord,
  title3d: Title3d,
  blob_card: BlobCard,
  serif_title: SerifTitle,
  numbered_point: NumberedPoint,
  handwritten: Handwritten,
  arc_letters: ArcLetters,
  sticker: Sticker,
};

export const getStyleComponent = (styleId: string): React.FC<StyleComponentProps> => {
  const component = STYLE_REGISTRY[styleId];
  if (!component) {
    console.warn(
      `[DynamicCaptionsStudio] Unknown style "${styleId}". Rendering safe fallback "pill_word".`
    );
    return PillWord;
  }
  return component;
};
