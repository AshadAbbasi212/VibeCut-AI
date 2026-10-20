import React, { useMemo } from "react";
import {
  AbsoluteFill,
  CalculateMetadataFunction,
  OffthreadVideo,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Timeline, TimelineEvent, TimelineWord } from "../types/timeline";
import { getStyleComponent } from "../styles/registry";
import { ensureFontsLoaded } from "../load-font";
import { GraphicRenderer, ArrowDoodle } from "../decorations";
import { popIn } from "../anim";

export type CaptionedVideoProps = {
  timeline?: Timeline;
  version?: number;
  video?: Timeline["video"];
  language?: string;
  words?: Timeline["words"];
  events?: Timeline["events"];
  [key: string]: unknown;
};

export const resolveTimeline = (props: CaptionedVideoProps): Timeline => {
  if (props.timeline && props.timeline.video) {
    return props.timeline;
  }
  if (props.video) {
    return {
      version: props.version ?? 1,
      video: props.video,
      language: props.language ?? "en",
      words: props.words ?? [],
      events: props.events ?? [],
    };
  }
  return {
    version: 1,
    video: {
      src: "sample.mp4",
      width: 1080,
      height: 1920,
      fps: 30,
      durationSec: 5,
    },
    language: "en",
    words: [],
    events: [],
  };
};

export const calculateCaptionedVideoMetadata: CalculateMetadataFunction<CaptionedVideoProps> = async ({
  props,
}) => {
  const timeline = resolveTimeline(props);
  const fps = timeline.video.fps || 30;
  const durationSec = timeline.video.durationSec || 10;
  const durationInFrames = Math.max(1, Math.round(durationSec * fps));
  const width = timeline.video.width || 1080;
  const height = timeline.video.height || 1920;

  return {
    fps,
    durationInFrames,
    width,
    height,
    props: {
      ...props,
      timeline,
    },
  };
};

const getZoneStyle = (event: TimelineEvent, timeline?: Timeline): React.CSSProperties => {
  const base: React.CSSProperties = {
    position: "absolute",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    width: "100%",
    paddingLeft: "6%",
    paddingRight: "6%",
    boxSizing: "border-box",
    zIndex: event.layer || 1,
    pointerEvents: "none",
  };

  // If user custom-dragged position is set (via event.y or global timeline.subtitleY)
  const customY = event.y ?? (event.zone === "lower" || event.zone === "free" ? timeline?.subtitleY : undefined);
  if (customY !== undefined && customY !== null) {
    const topPct = customY * 100;
    const leftPct = (event.x ?? 0.5) * 100;
    return {
      ...base,
      top: `${topPct}%`,
      left: `${leftPct}%`,
      transform: "translate(-50%, -50%)",
      width: "auto",
      maxWidth: "92%",
    };
  }

  switch (event.zone) {
    case "upper":
      return {
        ...base,
        top: "18%",
        transform: "translateY(-50%)",
      };
    case "center":
      return {
        ...base,
        top: "50%",
        transform: "translateY(-50%)",
      };
    case "lower":
    default:
      return {
        ...base,
        top: "79%",
        transform: "translateY(-50%)",
      };
    case "free": {
      const topPct = (event.y ?? 0.79) * 100;
      const leftPct = (event.x ?? 0.5) * 100;
      return {
        ...base,
        top: `${topPct}%`,
        left: `${leftPct}%`,
        transform: "translate(-50%, -50%)",
        width: "auto",
      };
    }
  }
};

const EventContainer: React.FC<{
  event: TimelineEvent;
  words: TimelineWord[];
  durationInFrames: number;
}> = ({ event, words, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const Component = getStyleComponent(event.style);

  const graphicScale = popIn(frame, fps, 0, 10, 0.45, 180);
  const doodleProgress = Math.min(1, Math.max(0, (frame - 4) / (fps * 0.45)));

  return (
    <div
      style={{
        position: "relative",
        display: "inline-flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {/* Attached Graphic (above/below/left/right) if not sticker */}
      {event.graphic && event.style !== "sticker" && (
        <div
          style={{
            transform: `scale(${graphicScale})`,
            marginBottom: event.graphic.position === "above" ? "14px" : undefined,
            marginTop: event.graphic.position === "below" ? "14px" : undefined,
            position:
              event.graphic.position === "left" || event.graphic.position === "right"
                ? "absolute"
                : "relative",
            left: event.graphic.position === "left" ? "-75px" : undefined,
            right: event.graphic.position === "right" ? "-75px" : undefined,
            top:
              event.graphic.position === "left" || event.graphic.position === "right"
                ? "50%"
                : undefined,
            transformOrigin: "center center",
          }}
        >
          <GraphicRenderer graphic={event.graphic} size={64} />
        </div>
      )}

      {/* Main Style Component */}
      <Component
        event={event}
        words={words}
        durationInFrames={durationInFrames}
      />

      {/* Optional Attached Arrow Doodle */}
      {event.decorations?.includes("arrow") && (
        <ArrowDoodle
          progress={doodleProgress}
          style={{
            top: "-40px",
            right: "-90px",
            transform: "rotate(15deg)",
          }}
        />
      )}
    </div>
  );
};

export const CaptionedVideo: React.FC<CaptionedVideoProps> = (props) => {
  useMemo(() => {
    ensureFontsLoaded();
  }, []);

  const timeline = resolveTimeline(props);
  const fps = timeline.video.fps || 30;

  // Resolve video source: if relative without slash or in jobs/, use staticFile or direct
  const videoSrc = useMemo(() => {
    const raw = timeline.video.src;
    if (raw.startsWith("http://") || raw.startsWith("https://")) {
      return raw;
    }
    return staticFile(raw);
  }, [timeline.video.src]);

  const layout = timeline.videoLayout || timeline.video.layout || "fill";
  const isVerticalComp = (timeline.video.width || 1080) < (timeline.video.height || 1920);
  const isSourceLandscape =
    timeline.video.originalWidth && timeline.video.originalHeight
      ? timeline.video.originalWidth > timeline.video.originalHeight
      : true;

  const renderVideoLayer = () => {
    // 1. Podcast Split-Screen (Stacked Dual-Cam: Top Host / Bottom Guest)
    if (layout === "split_podcast" && isVerticalComp && isSourceLandscape) {
      return (
        <AbsoluteFill style={{ backgroundColor: "#0b0c10" }}>
          {/* Top Speaker: Left side of 16:9 frame */}
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "50%",
              overflow: "hidden",
              backgroundColor: "#0d0e15",
            }}
          >
            <OffthreadVideo
              src={videoSrc}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                objectPosition: "15% center",
              }}
            />
          </div>

          {/* Bottom Speaker: Right side of 16:9 frame */}
          <div
            style={{
              position: "absolute",
              top: "50%",
              left: 0,
              width: "100%",
              height: "50%",
              overflow: "hidden",
              backgroundColor: "#0d0e15",
            }}
          >
            <OffthreadVideo
              src={videoSrc}
              muted
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                objectPosition: "85% center",
              }}
            />
          </div>

          {/* Broadcast Studio Sleek Divider Line with Cyan Neon Glow */}
          <div
            style={{
              position: "absolute",
              top: "50%",
              left: 0,
              width: "100%",
              height: "4px",
              transform: "translateY(-50%)",
              background:
                "linear-gradient(90deg, rgba(255,255,255,0.05), rgba(56, 189, 248, 0.75), rgba(255, 255, 255, 0.95), rgba(56, 189, 248, 0.75), rgba(255,255,255,0.05))",
              boxShadow:
                "0 0 16px rgba(56, 189, 248, 0.65), 0 2px 10px rgba(0, 0, 0, 0.8)",
              zIndex: 3,
            }}
          />
        </AbsoluteFill>
      );
    }

    // 2. Ambient Frosted Glass Mirror Background
    if (layout === "blur_fit" && isVerticalComp) {
      return (
        <AbsoluteFill style={{ backgroundColor: "#050608", overflow: "hidden" }}>
          {/* Zoomed & Blurred Mirror Background */}
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "100%",
              transform: "scale(1.8)",
              filter: "blur(45px) brightness(0.42)",
              overflow: "hidden",
            }}
          >
            <OffthreadVideo
              src={videoSrc}
              muted
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
              }}
            />
          </div>

          {/* Foreground Crisp Video with Soft Drop Shadow & Clean Border */}
          <div
            style={{
              position: "absolute",
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
              width: "100%",
              maxHeight: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 25px 60px rgba(0, 0, 0, 0.85)",
              zIndex: 2,
            }}
          >
            <OffthreadVideo
              src={videoSrc}
              style={{
                width: "100%",
                height: "auto",
                borderRadius: "14px",
              }}
            />
          </div>
        </AbsoluteFill>
      );
    }

    // 3. Left Speaker Focus (Cover cropped to left third)
    if (layout === "focus_left") {
      return (
        <AbsoluteFill style={{ backgroundColor: "#000" }}>
          <OffthreadVideo
            src={videoSrc}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              objectPosition: "15% center",
            }}
          />
        </AbsoluteFill>
      );
    }

    // 4. Right Speaker Focus (Cover cropped to right third)
    if (layout === "focus_right") {
      return (
        <AbsoluteFill style={{ backgroundColor: "#000" }}>
          <OffthreadVideo
            src={videoSrc}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              objectPosition: "85% center",
            }}
          />
        </AbsoluteFill>
      );
    }

    // 5. Standard Full Zoom / Center Cover Crop (Default for native 9:16 or fill mode)
    return (
      <AbsoluteFill style={{ backgroundColor: "#000" }}>
        <OffthreadVideo
          src={videoSrc}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            objectPosition: "center center",
          }}
        />
      </AbsoluteFill>
    );
  };

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Background Video Layer */}
      {renderVideoLayer()}

      {/* Dynamic Caption Events */}
      {timeline.events.map((rawEvent) => {
        const event: TimelineEvent = {
          ...rawEvent,
          captionSize: rawEvent.captionSize || timeline.captionSize || "medium",
          backgroundStyle: rawEvent.backgroundStyle || timeline.backgroundStyle || "transparent",
          highlightColor: rawEvent.highlightColor || timeline.highlightColor || "#38BDF8",
        };

        // When a feature event is active for this phrase window, suppress the redundant
        // base caption so only one clean, styled caption is visible at a time.
        if (event.id.startsWith("base_")) {
          const hasConcurrentFeature = timeline.events.some(
            (other) =>
              !other.id.startsWith("base_") &&
              Math.max(event.start, other.start) < Math.min(event.end, other.end)
          );
          if (hasConcurrentFeature) {
            return null;
          }
        }

        const from = Math.round(event.start * fps);
        const durationInFrames = Math.max(
          1,
          Math.round((event.end - event.start) * fps)
        );

        return (
          <Sequence
            key={event.id}
            from={from}
            durationInFrames={durationInFrames}
          >
            <div style={getZoneStyle(event, timeline)}>
              <EventContainer
                event={event}
                words={timeline.words}
                durationInFrames={durationInFrames}
              />
            </div>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
