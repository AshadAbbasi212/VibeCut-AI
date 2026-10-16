import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { twinkle } from "../anim";

export const Sparkles: React.FC<{
  size?: number;
  color?: string;
  style?: React.CSSProperties;
  phaseOffset?: number;
}> = ({ size = 36, color = "#FDE047", style, phaseOffset = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { scale, rotation } = twinkle(frame, fps, phaseOffset);

  return (
    <div
      style={{
        display: "inline-block",
        transform: `scale(${scale}) rotate(${rotation}deg)`,
        transformOrigin: "center center",
        ...style,
      }}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill={color}
        style={{ filter: `drop-shadow(0 0 8px ${color}88)` }}
      >
        <path d="M12 0C12 7 17 12 24 12C17 12 12 17 12 24C12 17 7 12 0 12C7 12 12 7 12 0Z" />
      </svg>
    </div>
  );
};

export const EllipseDoodle: React.FC<{
  width?: number;
  height?: number;
  strokeColor?: string;
  strokeWidth?: number;
  progress?: number;
  style?: React.CSSProperties;
}> = ({
  width = 380,
  height = 140,
  strokeColor = "#FFFFFF",
  strokeWidth = 3.5,
  progress = 1,
  style,
}) => {
  // Approximate perimeter of an ellipse
  const perimeter = Math.PI * (1.5 * (width + height) - Math.sqrt(width * height));
  const dashoffset = perimeter * (1 - Math.min(1, Math.max(0, progress)));

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      style={{
        position: "absolute",
        pointerEvents: "none",
        overflow: "visible",
        ...style,
      }}
    >
      <ellipse
        cx={width / 2}
        cy={height / 2}
        rx={width / 2 - 8}
        ry={height / 2 - 8}
        fill="none"
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeDasharray={perimeter}
        strokeDashoffset={dashoffset}
        style={{
          filter: "drop-shadow(0 2px 4px rgba(0,0,0,0.3))",
        }}
      />
    </svg>
  );
};

export const UnderlineScribble: React.FC<{
  width?: number;
  color?: string;
  progress?: number;
  style?: React.CSSProperties;
}> = ({ width = 280, color = "#FDE047", progress = 1, style }) => {
  const pathLength = width * 1.2;
  const dashoffset = pathLength * (1 - Math.min(1, Math.max(0, progress)));

  return (
    <svg
      width={width}
      height={28}
      viewBox={`0 0 ${width} 28`}
      style={{
        position: "absolute",
        bottom: "-14px",
        left: "50%",
        transform: "translateX(-50%)",
        overflow: "visible",
        ...style,
      }}
    >
      <path
        d={`M 4 14 Q ${width * 0.25} 6, ${width * 0.5} 14 T ${width - 4} 14`}
        fill="none"
        stroke={color}
        strokeWidth={4}
        strokeLinecap="round"
        strokeDasharray={pathLength}
        strokeDashoffset={dashoffset}
        style={{ filter: `drop-shadow(0 0 6px ${color}88)` }}
      />
    </svg>
  );
};
