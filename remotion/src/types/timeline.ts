export type Zone = "upper" | "center" | "lower" | "free";

export type HighlightKind = "color" | "italic" | "pill" | "underline" | "scale";

export interface TimelineHighlight {
  wordIndex: number;
  kind: HighlightKind;
  value: string;
}

export interface TimelineGraphic {
  kind: "emoji" | "icon" | "image" | "sticker3d";
  value: string;
  position?: "above" | "below" | "left" | "right";
}

export interface TimelineAnimation {
  in?: "pop" | "slide_up" | "fade" | "typewriter" | "none";
  out?: "fade" | "pop" | "none";
  wordStagger?: number;
}

export interface TimelineEvent {
  id: string;
  style: string;
  start: number;
  end: number;
  zone: Zone;
  x?: number;
  y?: number;
  layer: number;
  wordRange: [number, number] | number[];
  text: string;
  lines?: string[];
  highlights?: TimelineHighlight[];
  palette?: string;
  decorations?: string[];
  graphic?: TimelineGraphic | null;
  animation?: TimelineAnimation | null;
  variant?: string;
  captionSize?: "small" | "medium" | "large" | string;
  backgroundStyle?: "transparent" | "glass" | "solid";
  highlightColor?: string;
  sentenceId?: string;
}

export interface TimelineWord {
  i: number;
  text: string;
  start: number;
  end: number;
}

export interface CameraCut {
  start: number;
  end: number;
  focusX: number;
  speakerId?: string;
  layout?: "solo" | "split_duo" | "split_trio" | "wide";
}

export interface TimelineVideo {
  src: string;
  width: number;
  height: number;
  fps: number;
  durationSec: number;
  layout?: "split_podcast" | "split_triple" | "blur_fit" | "fill" | "focus_left" | "focus_right" | "active_speaker";
  originalWidth?: number;
  originalHeight?: number;
}

export interface Timeline {
  version: number;
  video: TimelineVideo;
  language: string;
  words: TimelineWord[];
  events: TimelineEvent[];
  captionSize?: "small" | "medium" | "large" | string;
  backgroundStyle?: "transparent" | "glass" | "solid";
  highlightColor?: string;
  subtitleY?: number;
  videoLayout?: "split_podcast" | "split_triple" | "blur_fit" | "fill" | "focus_left" | "focus_right" | "active_speaker";
  cameraCuts?: CameraCut[];
  progressBar?: boolean;
  progressBarPosition?: "bottom" | "top";
  headlineHook?: string;
  headlineStyle?: "badge" | "glass" | "clean" | "cyber";
  headlineDuration?: number;
  autoEmojis?: boolean;
}
