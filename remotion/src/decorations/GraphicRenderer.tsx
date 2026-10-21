import React from "react";
import * as LucideIcons from "lucide-react";
import { staticFile } from "remotion";
import { TimelineGraphic } from "../types/timeline";

interface GraphicRendererProps {
  graphic: TimelineGraphic;
  size?: number;
  glowColor?: string;
  style?: React.CSSProperties;
}

// Convert kebab-case or snake_case to PascalCase for Lucide icon lookup
const toPascalCase = (str: string): string => {
  return str
    .split(/[-_]/)
    .map((seg) => seg.charAt(0).toUpperCase() + seg.slice(1).toLowerCase())
    .join("");
};

// Map emojis to high-resolution 3D stickers
const EMOJI_TO_3D: Record<string, string> = {
  "🔥": "fire",
  "🚀": "rocket",
  "💰": "money_bag",
  "💵": "coin",
  "🪙": "coin",
  "💎": "diamond",
  "💡": "lightbulb",
  "🧠": "brain",
  "🤔": "brain",
  "🏆": "trophy",
  "🎯": "target",
  "⚡": "lightning",
  "⭐": "star",
  "🌟": "star",
  "✨": "star",
  "❤️": "heart",
  "💔": "heart",
  "🛑": "stop",
  "🔒": "lock",
  "🔑": "key",
  "👑": "crown",
  "📈": "chart",
  "📊": "chart",
  "💥": "boom",
  "👀": "eyes",
  "⚠️": "warning",
  "⏰": "clock",
  "⏳": "clock",
  "🎉": "party",
  "🤖": "robot",
  "🤑": "money_bag",
};

// Map icons to high-resolution 3D stickers
const ICON_TO_3D: Record<string, string> = {
  "zap": "lightning",
  "lightbulb": "lightbulb",
  "target": "target",
  "trending-up": "chart",
  "sparkles": "star",
  "shield": "lock",
};

export const GraphicRenderer: React.FC<GraphicRendererProps> = ({
  graphic,
  size = 78,
  glowColor = "rgba(56, 189, 248, 0.85)",
  style,
}) => {
  const { kind, value } = graphic;

  // 1. Explicit 3D Sticker
  if (kind === "sticker3d") {
    const src = staticFile(`stickers_3d/${value}.png`);
    return (
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          filter: `drop-shadow(0 14px 26px rgba(0, 0, 0, 0.75)) drop-shadow(0 0 20px ${glowColor})`,
          transform: "perspective(600px) rotateX(4deg)",
          ...style,
        }}
      >
        <img
          src={src}
          alt={value}
          style={{
            width: `${size}px`,
            height: `${size}px`,
            objectFit: "contain",
          }}
        />
      </div>
    );
  }

  // 2. Emoji automatically upgraded to 3D Sticker if available
  if (kind === "emoji") {
    const stickerName = EMOJI_TO_3D[value];
    if (stickerName) {
      const src = staticFile(`stickers_3d/${stickerName}.png`);
      return (
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            filter: `drop-shadow(0 14px 26px rgba(0, 0, 0, 0.75)) drop-shadow(0 0 20px ${glowColor})`,
            transform: "perspective(600px) rotateX(4deg)",
            ...style,
          }}
        >
          <img
            src={src}
            alt={value}
            style={{
              width: `${size}px`,
              height: `${size}px`,
              objectFit: "contain",
            }}
          />
        </div>
      );
    }
  }

  // 3. Icon automatically upgraded to 3D Sticker if available
  if (kind === "icon") {
    const stickerName = ICON_TO_3D[value];
    if (stickerName) {
      const src = staticFile(`stickers_3d/${stickerName}.png`);
      return (
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            filter: `drop-shadow(0 14px 26px rgba(0, 0, 0, 0.75)) drop-shadow(0 0 20px ${glowColor})`,
            transform: "perspective(600px) rotateX(4deg)",
            ...style,
          }}
        >
          <img
            src={src}
            alt={value}
            style={{
              width: `${size}px`,
              height: `${size}px`,
              objectFit: "contain",
            }}
          />
        </div>
      );
    }

    const iconName = toPascalCase(value);
    const IconComponent = (LucideIcons as unknown as Record<string, React.FC<{ size?: number; color?: string; strokeWidth?: number }>>)[
      iconName
    ];

    if (IconComponent) {
      return (
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            filter: `drop-shadow(0 0 16px ${glowColor}) drop-shadow(0 0 30px ${glowColor})`,
            ...style,
          }}
        >
          <IconComponent size={size} color="#FFFFFF" strokeWidth={2.5} />
        </div>
      );
    }
  }

  // 4. Custom image
  if (kind === "image") {
    const src = value.startsWith("http") ? value : staticFile(value);
    return (
      <img
        src={src}
        alt=""
        style={{
          width: `${size}px`,
          height: `${size}px`,
          objectFit: "contain",
          filter: `drop-shadow(0 10px 20px rgba(0,0,0,0.6)) drop-shadow(0 0 16px ${glowColor})`,
          ...style,
        }}
      />
    );
  }

  // 5. Fallback standard emoji
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: `${size}px`,
        lineHeight: 1,
        filter: `drop-shadow(0 0 16px ${glowColor}) drop-shadow(0 0 32px ${glowColor})`,
        ...style,
      }}
    >
      {value}
    </div>
  );
};

