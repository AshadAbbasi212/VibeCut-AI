import React, { useMemo } from "react";
import {
  AbsoluteFill,
  CalculateMetadataFunction,
  OffthreadVideo,
  Sequence,
  staticFile,
} from "remotion";
import { Timeline, TimelineEvent } from "../types/timeline";
import { PillWord } from "../styles/pill_word";
import { ensureFontsLoaded } from "../load-font";

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
              <PillWord
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
