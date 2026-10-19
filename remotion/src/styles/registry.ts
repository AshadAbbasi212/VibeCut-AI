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
import { NeonGlow } from "./neon_glow";
import { TypewriterTerminal } from "./typewriter_terminal";
import { PaperCutout } from "./paper_cutout";
import { GlitchKinetic } from "./glitch_kinetic";
import { QuoteEditorial } from "./quote_editorial";
import { ComicBubble } from "./comic_bubble";
import { GradientOutline } from "./gradient_outline";
import { MinimalUnderline } from "./minimal_underline";

export interface StyleComponentProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const getCaptionFontSize = (
  size?: "small" | "medium" | "large" | string,
  base: number = 52
): number => {
  if (size === "small") return Math.round(base * 0.74);
  if (size === "large") return Math.round(base * 1.30);
  return base;
};

export const STYLE_REGISTRY: Record<string, React.FC<StyleComponentProps>> = {
  pill_word: PillWord,
  title3d: Title3d,
  blob_card: BlobCard,
  serif_title: SerifTitle,
  numbered_point: NumberedPoint,
  handwritten: Handwritten,
  arc_letters: ArcLetters,
  sticker: Sticker,
  neon_glow: NeonGlow,
  typewriter_terminal: TypewriterTerminal,
  paper_cutout: PaperCutout,
  glitch_kinetic: GlitchKinetic,
  quote_editorial: QuoteEditorial,
  comic_bubble: ComicBubble,
  gradient_outline: GradientOutline,
  minimal_underline: MinimalUnderline,
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
