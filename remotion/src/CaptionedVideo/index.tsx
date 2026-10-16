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

const getZoneStyle = (event: TimelineEvent): React.CSSProperties => {
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

  switch (event.zone) {
    case "upper":
      return {
        ...base,
        top: "20%",
        transform: "translateY(-50%)",
      };
    case "center":
      return {
        ...base,
        top: "48%",
        transform: "translateY(-50%)",
      };
    case "lower":
    default:
      return {
        ...base,
        top: "74%",
        transform: "translateY(-50%)",
      };
    case "free": {
      const topPct = (event.y ?? 0.74) * 100;
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

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Background Video */}
      <AbsoluteFill>
        <OffthreadVideo
          src={videoSrc}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
        />
      </AbsoluteFill>

      {/* Dynamic Caption Events */}
      {timeline.events.map((event) => {
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
            <div style={getZoneStyle(event)}>
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
