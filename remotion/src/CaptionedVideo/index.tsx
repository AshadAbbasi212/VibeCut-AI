import React, { useMemo } from "react";
import {
  AbsoluteFill,
  Audio,
  CalculateMetadataFunction,
  OffthreadVideo,
  Sequence,
  interpolate,
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
    zIndex: (event.layer || 1) + 20,
    pointerEvents: "none",
  };

  // Safe headmarker and face clearance:
  // In vertical video, the headmarker is at 8%-22% (top), and the speaker's face is at 30%-55% (center).
  // Captions must NEVER render behind the headmarker (upper) or on top of the speaker's face (center).
  const hasHeadmarker = Boolean(timeline?.headlineHook && timeline.headlineHook.trim());

  let zone = event.zone || "lower";
  let targetY = event.y ?? (zone === "lower" || zone === "free" ? timeline?.subtitleY : undefined);
  let targetX = event.x ?? 0.5;

  if (hasHeadmarker && (zone === "upper" || (targetY !== undefined && targetY < 0.28))) {
    const dialogueY = timeline?.subtitleY ?? 0.79;
    targetY = Math.max(0.62, dialogueY - 0.11);
    targetX = 0.5;
    zone = "free";
  } else if (zone === "center" || (targetY !== undefined && targetY >= 0.35 && targetY <= 0.58)) {
    const dialogueY = timeline?.subtitleY ?? 0.79;
    targetY = Math.max(0.62, dialogueY - 0.11);
    targetX = 0.5;
    zone = "free";
  }

  // Left-flank editorial callout (Ali Abdaal side highlight)
  if ((zone as string) === "left" || (zone === "free" && targetX <= 0.35 && (targetY ?? 0.70) >= 0.65)) {
    return {
      ...base,
      top: `${(targetY ?? 0.70) * 100}%`,
      left: `${(targetX ?? 0.26) * 100}%`,
      width: "auto",
      maxWidth: "46%",
      transform: "translate(-50%, -50%)",
      alignItems: "flex-start",
      textAlign: "left",
    };
  }

  // Right-flank editorial callout (Ali Abdaal side highlight)
  if ((zone as string) === "right" || (zone === "free" && targetX >= 0.65 && (targetY ?? 0.70) >= 0.65)) {
    return {
      ...base,
      top: `${(targetY ?? 0.70) * 100}%`,
      left: `${(targetX ?? 0.74) * 100}%`,
      width: "auto",
      maxWidth: "46%",
      transform: "translate(-50%, -50%)",
      alignItems: "flex-end",
      textAlign: "right",
    };
  }

  // If user custom-dragged position is set or zone is free/callout_stack
  const customY = targetY ?? timeline?.subtitleY ?? 0.79;
  const leftPct = targetX * 100;
  return {
    ...base,
    top: `${customY * 100}%`,
    left: `${leftPct}%`,
    transform: "translate(-50%, -50%)",
    width: "auto",
    maxWidth: "92%",
  };
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
          <GraphicRenderer graphic={event.graphic} size={76} />
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
  const { fps: videoConfigFps, durationInFrames } = useVideoConfig();
  const fps = timeline.video.fps || videoConfigFps || 30;

  // Resolve video source: if relative without slash or in jobs/, use staticFile or direct
  const videoSrc = useMemo(() => {
    const raw = timeline.video.src;
    if (raw.startsWith("http://") || raw.startsWith("https://")) {
      return raw;
    }
    return staticFile(raw);
  }, [timeline.video.src]);

  const frame = useCurrentFrame();
  const currentTime = frame / fps;

  const layout = timeline.videoLayout || timeline.video.layout || "fill";
  const isVerticalComp = (timeline.video.width || 1080) < (timeline.video.height || 1920);
  const isSourceLandscape =
    timeline.video.originalWidth && timeline.video.originalHeight
      ? timeline.video.originalWidth > timeline.video.originalHeight
      : true;

  const renderProgressBar = () => {
    if (timeline.progressBar === false) return null;
    const isTop = timeline.progressBarPosition === "top";
    const totalFrames = durationInFrames || Math.max(1, Math.round(timeline.video.durationSec * fps));
    const progressPct = Math.min(100, Math.max(0, (frame / totalFrames) * 100));
    const accentColor = timeline.highlightColor || "#38BDF8";

    return (
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: isTop ? 0 : undefined,
          bottom: !isTop ? 0 : undefined,
          height: "10px",
          backgroundColor: "rgba(0, 0, 0, 0.4)",
          backdropFilter: "blur(8px)",
          WebkitBackdropFilter: "blur(8px)",
          zIndex: 95,
          overflow: "hidden",
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${progressPct}%`,
            background: `linear-gradient(90deg, ${accentColor}, #ec4899, #FBBF24)`,
            boxShadow: `0 0 16px ${accentColor}`,
            borderRadius: "0 4px 4px 0",
          }}
        />
      </div>
    );
  };

  const renderHeadlineHook = () => {
    if (!timeline.headlineHook || !timeline.headlineHook.trim()) return null;

    let fadeOpacity = 1;
    if (timeline.headlineDuration && timeline.headlineDuration > 0) {
      const maxFrame = Math.round(timeline.headlineDuration * fps);
      if (frame >= maxFrame) return null;
      if (frame >= maxFrame - 15) {
        fadeOpacity = interpolate(frame, [maxFrame - 15, maxFrame], [1, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
      }
    }

    const hookScale = popIn(frame, fps, 2, 12, 0.5, 160);
    const hookStyleType = timeline.headlineStyle || "badge";
    const fonts = ensureFontsLoaded();

    let cardStyle: React.CSSProperties = {};
    if (hookStyleType === "badge") {
      cardStyle = {
        background: "linear-gradient(135deg, rgba(20, 20, 26, 0.94), rgba(10, 10, 15, 0.98))",
        border: "2.5px solid #F59E0B",
        borderRadius: "9999px",
        boxShadow: "0 16px 36px rgba(0, 0, 0, 0.75), 0 0 25px rgba(245, 158, 11, 0.35)",
        color: "#FFFFFF",
        fontFamily: fonts.sans,
        fontWeight: 900,
        fontSize: "30px",
        letterSpacing: "1px",
        padding: "14px 34px",
        textTransform: "uppercase",
      };
    } else if (hookStyleType === "glass") {
      cardStyle = {
        background: "rgba(255, 255, 255, 0.14)",
        backdropFilter: "blur(24px)",
        WebkitBackdropFilter: "blur(24px)",
        border: "1.5px solid rgba(255, 255, 255, 0.32)",
        borderRadius: "20px",
        boxShadow: "0 20px 45px rgba(0, 0, 0, 0.55), inset 0 1px 1px rgba(255, 255, 255, 0.4)",
        color: "#FFFFFF",
        fontFamily: fonts.sans,
        fontWeight: 800,
        fontSize: "32px",
        padding: "16px 36px",
        textShadow: "0 2px 10px rgba(0, 0, 0, 0.7)",
      };
    } else if (hookStyleType === "clean") {
      cardStyle = {
        background: "#FFFFFF",
        color: "#09090B",
        borderRadius: "14px",
        border: "3px solid #000000",
        boxShadow: "0 16px 36px rgba(0, 0, 0, 0.7)",
        fontFamily: fonts.sans,
        fontWeight: 900,
        fontSize: "32px",
        letterSpacing: "-0.5px",
        padding: "14px 32px",
      };
    } else if (hookStyleType === "cyber") {
      cardStyle = {
        background: "rgba(10, 10, 24, 0.94)",
        border: "2.5px solid #00F0FF",
        borderRadius: "10px",
        boxShadow: "0 0 30px rgba(0, 240, 255, 0.45), inset 0 0 15px rgba(0, 240, 255, 0.2)",
        color: "#00F0FF",
        fontFamily: fonts.mono,
        fontWeight: 900,
        fontSize: "30px",
        letterSpacing: "2.5px",
        textTransform: "uppercase",
        padding: "14px 32px",
      };
    }

    const hookYRatio = timeline.headlineY !== undefined && timeline.headlineY !== null ? timeline.headlineY : 0.08;
    const hookYTop = `${Math.round(hookYRatio * 1000) / 10}%`;

    return (
      <div
        style={{
          position: "absolute",
          top: hookYTop,
          left: "50%",
          transform: `translateX(-50%) scale(${hookScale})`,
          opacity: fadeOpacity,
          maxWidth: "88%",
          zIndex: 85,
          pointerEvents: "none",
          textAlign: "center",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div style={cardStyle}>
          {timeline.headlineHook}
        </div>
      </div>
    );
  };

  const renderVideoLayer = () => {
    // 0. Active Speaker Auto-Tracking (Dynamic Speaker Cuts with Cross-Talk Fallback)
    if (layout === "active_speaker" && isVerticalComp && isSourceLandscape) {
      const activeCut = timeline.cameraCuts?.find(
        (cut) => currentTime >= cut.start && currentTime < cut.end
      ) || timeline.cameraCuts?.[0];

      const currentFocusX = activeCut ? activeCut.focusX : 0.5;
      const currentCutLayout = activeCut ? activeCut.layout : "solo";

      // If cross-talk or interruption, cut to Split Stack
      if (currentCutLayout === "split_duo") {
        return (
          <AbsoluteFill style={{ backgroundColor: "#0b0c10" }}>
            <div style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "50%", overflow: "hidden", backgroundColor: "#0d0e15" }}>
              <OffthreadVideo src={videoSrc} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "20% center" }} />
            </div>
            <div style={{ position: "absolute", top: "50%", left: 0, width: "100%", height: "50%", overflow: "hidden", backgroundColor: "#0d0e15" }}>
              <OffthreadVideo src={videoSrc} muted style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "82% center" }} />
            </div>
            <div style={{ position: "absolute", top: "50%", left: 0, width: "100%", height: "4px", transform: "translateY(-50%)", background: "linear-gradient(90deg, rgba(255,255,255,0.05), rgba(56, 189, 248, 0.75), rgba(255, 255, 255, 0.95), rgba(56, 189, 248, 0.75), rgba(255,255,255,0.05))", boxShadow: "0 0 16px rgba(56, 189, 248, 0.65), 0 2px 10px rgba(0, 0, 0, 0.8)", zIndex: 3 }} />
          </AbsoluteFill>
        );
      }

      if (currentCutLayout === "split_trio") {
        return (
          <AbsoluteFill style={{ backgroundColor: "#0b0c10" }}>
            <div style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "33.33%", overflow: "hidden", backgroundColor: "#0d0e15" }}>
              <OffthreadVideo src={videoSrc} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "15% center" }} />
            </div>
            <div style={{ position: "absolute", top: "33.33%", left: 0, width: "100%", height: "33.34%", overflow: "hidden", backgroundColor: "#0d0e15" }}>
              <OffthreadVideo src={videoSrc} muted style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center center" }} />
            </div>
            <div style={{ position: "absolute", top: "66.67%", left: 0, width: "100%", height: "33.33%", overflow: "hidden", backgroundColor: "#0d0e15" }}>
              <OffthreadVideo src={videoSrc} muted style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "85% center" }} />
            </div>
            <div style={{ position: "absolute", top: "33.33%", left: 0, width: "100%", height: "3px", transform: "translateY(-50%)", background: "linear-gradient(90deg, rgba(255,255,255,0.05), rgba(56, 189, 248, 0.75), rgba(255, 255, 255, 0.95), rgba(56, 189, 248, 0.75), rgba(255,255,255,0.05))", boxShadow: "0 0 12px rgba(56, 189, 248, 0.6)", zIndex: 3 }} />
            <div style={{ position: "absolute", top: "66.67%", left: 0, width: "100%", height: "3px", transform: "translateY(-50%)", background: "linear-gradient(90deg, rgba(255,255,255,0.05), rgba(56, 189, 248, 0.75), rgba(255, 255, 255, 0.95), rgba(56, 189, 248, 0.75), rgba(255,255,255,0.05))", boxShadow: "0 0 12px rgba(56, 189, 248, 0.6)", zIndex: 3 }} />
          </AbsoluteFill>
        );
      }

      // Solo Active Speaker Broadcast Shot
      return (
        <AbsoluteFill style={{ backgroundColor: "#000" }}>
          <OffthreadVideo
            src={videoSrc}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              objectPosition: `${currentFocusX * 100}% center`,
            }}
          />
        </AbsoluteFill>
      );
    }
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

    // 1b. 3-Person Panel Stack (Top / Middle / Bottom: Left, Center, Right)
    if (layout === "split_triple" && isVerticalComp && isSourceLandscape) {
      return (
        <AbsoluteFill style={{ backgroundColor: "#0b0c10" }}>
          {/* Top Speaker: Left side of 16:9 frame */}
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "33.33%",
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

          {/* Middle Speaker: Center of 16:9 frame */}
          <div
            style={{
              position: "absolute",
              top: "33.33%",
              left: 0,
              width: "100%",
              height: "33.34%",
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
                objectPosition: "center center",
              }}
            />
          </div>

          {/* Bottom Speaker: Right side of 16:9 frame */}
          <div
            style={{
              position: "absolute",
              top: "66.67%",
              left: 0,
              width: "100%",
              height: "33.33%",
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

          {/* Divider 1 at 33.33% */}
          <div
            style={{
              position: "absolute",
              top: "33.33%",
              left: 0,
              width: "100%",
              height: "3px",
              transform: "translateY(-50%)",
              background:
                "linear-gradient(90deg, rgba(255,255,255,0.05), rgba(56, 189, 248, 0.75), rgba(255, 255, 255, 0.95), rgba(56, 189, 248, 0.75), rgba(255,255,255,0.05))",
              boxShadow: "0 0 12px rgba(56, 189, 248, 0.6)",
              zIndex: 3,
            }}
          />

          {/* Divider 2 at 66.67% */}
          <div
            style={{
              position: "absolute",
              top: "66.67%",
              left: 0,
              width: "100%",
              height: "3px",
              transform: "translateY(-50%)",
              background:
                "linear-gradient(90deg, rgba(255,255,255,0.05), rgba(56, 189, 248, 0.75), rgba(255, 255, 255, 0.95), rgba(56, 189, 248, 0.75), rgba(255,255,255,0.05))",
              boxShadow: "0 0 12px rgba(56, 189, 248, 0.6)",
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

  // Kinetic punch-in zoom calculation (resets audience attention every ~5 seconds)
  let videoScale = 1.0;
  if (timeline.kineticZoom) {
    const cycle = frame % 150; // every 5 seconds (150 frames @ 30fps)
    if (cycle >= 0 && cycle <= 36) {
      if (cycle < 6) {
        videoScale = interpolate(cycle, [0, 6], [1.0, 1.13], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
      } else if (cycle > 30) {
        videoScale = interpolate(cycle, [30, 36], [1.13, 1.0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
      } else {
        videoScale = 1.13;
      }
    }
  }

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Background Video Layer with optional Kinetic Punch-In Zoom */}
      <div
        style={{
          width: "100%",
          height: "100%",
          transform: `scale(${videoScale})`,
          transformOrigin: "center center",
        }}
      >
        {renderVideoLayer()}
      </div>

      {/* Retention Progress Bar */}
      {renderProgressBar()}

      {/* Top Headline Hook Card (Optional user card) */}
      {renderHeadlineHook()}

      {/* Brand Watermark / Handle Badge */}
      {timeline.watermarkText && (
        <div
          style={{
            position: "absolute",
            top: 52,
            right: 52,
            display: "flex",
            alignItems: "center",
            gap: 8,
            background: "rgba(10, 10, 15, 0.75)",
            backdropFilter: "blur(14px)",
            WebkitBackdropFilter: "blur(14px)",
            border: "1px solid rgba(255, 255, 255, 0.18)",
            borderRadius: 9999,
            padding: "8px 22px",
            boxShadow: "0 10px 30px rgba(0, 0, 0, 0.6)",
            zIndex: 35,
          }}
        >
          <span style={{ fontSize: 18 }}>✨</span>
          <span
            style={{
              color: "#FFFFFF",
              fontFamily: "'Inter', sans-serif",
              fontWeight: 800,
              fontSize: 20,
              letterSpacing: "0.5px",
            }}
          >
            {timeline.watermarkText.startsWith("@")
              ? timeline.watermarkText
              : `@${timeline.watermarkText}`}
          </span>
        </div>
      )}

      {/* Lo-Fi Ambient Background Music (if enabled) */}
      {timeline.bgMusic && (
        <Audio
          src={staticFile("audio/bg_lofi.wav")}
          volume={timeline.bgMusicVolume || 0.12}
          loop
        />
      )}

      {/* Viral Pop Sound Effects on Hook and Graphic Sticker Entrances */}
      {timeline.soundEffects &&
        timeline.events
          .filter(
            (e) =>
              e.graphic ||
              e.style === "beast_impact" ||
              e.style === "title3d" ||
              e.style === "fire_burn"
          )
          .map((e) => (
            <Sequence
              key={`sfx_${e.id}`}
              from={Math.round(e.start * fps)}
              durationInFrames={8}
            >
              <Audio src={staticFile("audio/sfx_pop.wav")} volume={0.35} />
            </Sequence>
          ))}

      {/* Dynamic Caption Events */}
      {timeline.events.map((rawEvent) => {
        // Multi-Speaker Diarization Auto Color Coding
        let resolvedHighlightColor =
          rawEvent.highlightColor || timeline.highlightColor || "#38BDF8";
        if (rawEvent.speakerId === "speaker_1") {
          resolvedHighlightColor = "#F59E0B"; // Amber Gold for Guest / Speaker 2
        } else if (rawEvent.speakerId === "speaker_0") {
          resolvedHighlightColor = "#38BDF8"; // Electric Cyan for Host / Speaker 1
        }

        const event: TimelineEvent = {
          ...rawEvent,
          captionSize: rawEvent.captionSize || timeline.captionSize || "medium",
          backgroundStyle:
            rawEvent.backgroundStyle || timeline.backgroundStyle || "transparent",
          highlightColor: resolvedHighlightColor,
        };

        // When a feature event is active for this phrase window, suppress redundant base
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
