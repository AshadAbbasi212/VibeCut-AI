import React, { useMemo } from "react";
import { AbsoluteFill } from "remotion";
import { TimelineEvent, TimelineWord } from "../types/timeline";
import { STYLE_REGISTRY } from "../styles/registry";
import { ensureFontsLoaded } from "../load-font";

export interface StyleGalleryProps {
  styleId?: string;
  variant?: string;
  palette?: string;
  [key: string]: unknown;
}

export const SAMPLE_EVENTS: Record<string, TimelineEvent> = {
  title3d: {
    id: "g_title3d",
    style: "title3d",
    start: 0,
    end: 5,
    zone: "center",
    layer: 2,
    wordRange: [0, 6],
    text: "Making money is basically a skills problem",
    lines: ["MAKING MONEY", "IS BASICALLY A", "SKILLS PROBLEM"],
    palette: "sunset",
    decorations: ["sparkles"],
  },
  blob_card: {
    id: "g_blob_card",
    style: "blob_card",
    start: 0,
    end: 5,
    zone: "center",
    layer: 2,
    wordRange: [0, 6],
    text: "Everything that is a skill can be learnt",
    lines: ["Everything that is a skill", "✨ can be learnt ✨"],
    variant: "glow",
  },
  blob_card_frosted: {
    id: "g_blob_card_frosted",
    style: "blob_card",
    start: 0,
    end: 5,
    zone: "upper",
    layer: 2,
    wordRange: [0, 10],
    text: "If that person is NOT where you want to be, ignore their advice.",
    lines: [
      "If that person is NOT",
      "where you want to be,",
      "ignore their advice.",
    ],
    variant: "frosted",
  },
  pill_word: {
    id: "g_pill_word",
    style: "pill_word",
    start: 0,
    end: 5,
    zone: "lower",
    layer: 1,
    wordRange: [0, 4],
    text: "at least when you're driving,",
  },
  serif_title: {
    id: "g_serif_title",
    style: "serif_title",
    start: 0,
    end: 5,
    zone: "upper",
    layer: 2,
    wordRange: [0, 7],
    text: "How to STOP PLANNING and just TAKE ACTION",
    lines: ["How to", "STOP PLANNING", "and just TAKE ACTION"],
    decorations: ["ellipse"],
  },
  numbered_point: {
    id: "g_numbered_point",
    style: "numbered_point",
    start: 0,
    end: 5,
    zone: "upper",
    layer: 2,
    wordRange: [0, 7],
    text: "1 Having a way to monetise makes it easier",
    lines: ["Having a way", "to monetise makes", "it easier"],
    decorations: ["ellipse"],
  },
  handwritten: {
    id: "g_handwritten",
    style: "handwritten",
    start: 0,
    end: 5,
    zone: "upper",
    layer: 2,
    wordRange: [0, 5],
    text: "rather than a luck problem",
  },
  arc_letters: {
    id: "g_arc_letters",
    style: "arc_letters",
    start: 0,
    end: 5,
    zone: "center",
    layer: 2,
    wordRange: [0, 3],
    text: "B C D E",
  },
  sticker: {
    id: "g_sticker",
    style: "sticker",
    start: 0,
    end: 5,
    zone: "center",
    layer: 2,
    wordRange: [0, 0],
    text: "Doctor",
    graphic: { kind: "emoji", value: "🩺", position: "above" },
  },
  neon_glow: {
    id: "g_neon_glow",
    style: "neon_glow",
    start: 0,
    end: 5,
    zone: "center",
    layer: 2,
    wordRange: [0, 4],
    text: "Cyberpunk High Energy Glow",
  },
  typewriter_terminal: {
    id: "g_typewriter_terminal",
    style: "typewriter_terminal",
    start: 0,
    end: 5,
    zone: "center",
    layer: 2,
    wordRange: [0, 4],
    text: "npm run deploy --production",
  },
  paper_cutout: {
    id: "g_paper_cutout",
    style: "paper_cutout",
    start: 0,
    end: 5,
    zone: "center",
    layer: 2,
    wordRange: [0, 4],
    text: "Remember This Golden Rule",
  },
  glitch_kinetic: {
    id: "g_glitch_kinetic",
    style: "glitch_kinetic",
    start: 0,
    end: 5,
    zone: "center",
    layer: 2,
    wordRange: [0, 3],
    text: "DISRUPT THE MATRIX",
  },
  quote_editorial: {
    id: "g_quote_editorial",
    style: "quote_editorial",
    start: 0,
    end: 5,
    zone: "center",
    layer: 2,
    wordRange: [0, 5],
    text: "Simplicity is the ultimate sophistication",
  },
  comic_bubble: {
    id: "g_comic_bubble",
    style: "comic_bubble",
    start: 0,
    end: 5,
    zone: "center",
    layer: 2,
    wordRange: [0, 3],
    text: "WAIT, WHAT JUST HAPPENED?!",
  },
  gradient_outline: {
    id: "g_gradient_outline",
    style: "gradient_outline",
    start: 0,
    end: 5,
    zone: "center",
    layer: 2,
    wordRange: [0, 4],
    text: "LUMINOUS GRADIENT OUTLINE",
  },
  minimal_underline: {
    id: "g_minimal_underline",
    style: "minimal_underline",
    start: 0,
    end: 5,
    zone: "center",
    layer: 2,
    wordRange: [0, 4],
    text: "Focus on what truly matters",
  },
  hormozi_bold: {
    id: "g_hormozi_bold",
    style: "hormozi_bold",
    start: 0,
    end: 5,
    zone: "center",
    layer: 2,
    wordRange: [0, 4],
    text: "STOP PLANNING AND EXECUTE TODAY",
  },
  retro_vaporwave: {
    id: "g_retro_vaporwave",
    style: "retro_vaporwave",
    start: 0,
    end: 5,
    zone: "center",
    layer: 2,
    wordRange: [0, 4],
    text: "CYBERPUNK NEON RETROWAVE DREAMS",
  },
  karaoke_bounce: {
    id: "g_karaoke_bounce",
    style: "karaoke_bounce",
    start: 0,
    end: 5,
    zone: "center",
    layer: 2,
    wordRange: [0, 4],
    text: "Follow the bouncing golden rhythm",
  },
  fire_burn: {
    id: "g_fire_burn",
    style: "fire_burn",
    start: 0,
    end: 5,
    zone: "center",
    layer: 2,
    wordRange: [0, 4],
    text: "BLAZING HOT VIRAL HOOKS",
  },
  beast_impact: {
    id: "g_beast_impact",
    style: "beast_impact",
    start: 0,
    end: 5,
    zone: "center",
    layer: 2,
    wordRange: [0, 4],
    text: "MASSIVE RETENTION POP HOOK",
  },
  highlighter_marker: {
    id: "g_highlighter_marker",
    style: "highlighter_marker",
    start: 0,
    end: 5,
    zone: "center",
    layer: 2,
    wordRange: [0, 4],
    text: "Clean smart educational highlighter highlight",
  },
  cinematic_minimal: {
    id: "g_cinematic_minimal",
    style: "cinematic_minimal",
    start: 0,
    end: 5,
    zone: "lower",
    layer: 2,
    wordRange: [0, 4],
    text: "A24 cinematic documentary letterbox subtitle",
  },
  cyber_hud: {
    id: "g_cyber_hud",
    style: "cyber_hud",
    start: 0,
    end: 5,
    zone: "center",
    layer: 2,
    wordRange: [0, 4],
    text: "CYBERPUNK TELEMETRY HUD TARGET LOCKED",
  },
};

const SAMPLE_WORDS: TimelineWord[] = [
  { i: 0, text: "at", start: 0.0, end: 0.3 },
  { i: 1, text: "least", start: 0.3, end: 0.6 },
  { i: 2, text: "when", start: 0.6, end: 0.9 },
  { i: 3, text: "you're", start: 0.9, end: 1.2 },
  { i: 4, text: "driving,", start: 2.5, end: 3.0 }, // future word
];

export const StyleGallery: React.FC<StyleGalleryProps> = ({
  styleId = "title3d",
  variant,
  palette,
}) => {
  useMemo(() => {
    ensureFontsLoaded();
  }, []);

  // Determine which event to show
  const lookupKey =
    styleId === "blob_card" && variant === "frosted"
      ? "blob_card_frosted"
      : styleId;

  const baseEvent = SAMPLE_EVENTS[lookupKey] || SAMPLE_EVENTS.title3d;
  const event: TimelineEvent = {
    ...baseEvent,
    variant: variant ?? baseEvent.variant,
    palette: palette ?? baseEvent.palette,
  };

  const Component = STYLE_REGISTRY[event.style] || STYLE_REGISTRY.pill_word;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#18181B", // Dark sleek studio background
        backgroundImage:
          "radial-gradient(circle at 50% 30%, #27272A 0%, #09090B 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {/* Visual placement container */}
      <div
        style={{
          width: "100%",
          padding: "0 6%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          boxSizing: "border-box",
        }}
      >
        <Component
          event={event}
          words={SAMPLE_WORDS}
          durationInFrames={150}
        />
      </div>
    </AbsoluteFill>
  );
};
