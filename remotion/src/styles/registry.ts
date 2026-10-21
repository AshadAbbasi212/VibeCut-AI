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
import { HormoziBold } from "./hormozi_bold";
import { RetroVaporwave } from "./retro_vaporwave";
import { KaraokeBounce } from "./karaoke_bounce";
import { FireBurn } from "./fire_burn";
import { BeastImpact } from "./beast_impact";
import { HighlighterMarker } from "./highlighter_marker";
import { CinematicMinimal } from "./cinematic_minimal";
import { CyberHud } from "./cyber_hud";

export interface StyleComponentProps {
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}

export const getCaptionFontSize = (
  size?: "small" | "medium" | "large" | string,
  base: number = 52
): number => {
  if (!size) return base;
  if (size === "small") return Math.round(base * 0.74);
  if (size === "large") return Math.round(base * 1.30);
  if (size === "medium") return base;
  const num = parseFloat(size);
  if (!isNaN(num) && num >= 16 && num <= 160) {
    const scale = num / 52;
    return Math.round(base * scale);
  }
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
  hormozi_bold: HormoziBold,
  retro_vaporwave: RetroVaporwave,
  karaoke_bounce: KaraokeBounce,
  fire_burn: FireBurn,
  beast_impact: BeastImpact,
  highlighter_marker: HighlighterMarker,
  cinematic_minimal: CinematicMinimal,
  cyber_hud: CyberHud,
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
