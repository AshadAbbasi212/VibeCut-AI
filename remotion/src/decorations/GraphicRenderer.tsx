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

export const GraphicRenderer: React.FC<GraphicRendererProps> = ({
  graphic,
  size = 96,
  glowColor = "rgba(56, 189, 248, 0.85)",
  style,
}) => {
  const { kind, value } = graphic;

  if (kind === "icon") {
    const iconName = toPascalCase(value);
    // Lucide components are typed functions
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
          filter: `drop-shadow(0 0 16px ${glowColor})`,
          ...style,
        }}
      />
    );
  }

  // Default: emoji
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
