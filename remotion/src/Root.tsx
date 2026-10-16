import React from "react";
import { Composition } from "remotion";
import {
  CaptionedVideo,
  calculateCaptionedVideoMetadata,
  CaptionedVideoProps,
} from "./CaptionedVideo";

const defaultTimeline: CaptionedVideoProps["timeline"] = {
  version: 1,
  video: {
    src: "sample.mp4",
    width: 1080,
    height: 1920,
    fps: 30,
    durationSec: 5,
  },
  language: "en",
  words: [
    { i: 0, text: "Making", start: 0.1, end: 0.5 },
    { i: 1, text: "money", start: 0.5, end: 0.9 },
    { i: 2, text: "is", start: 0.9, end: 1.2 },
    { i: 3, text: "a", start: 1.2, end: 1.4 },
    { i: 4, text: "skills", start: 1.4, end: 1.8 },
    { i: 5, text: "problem", start: 1.8, end: 2.4 },
  ],
  events: [
    {
      id: "e1",
      style: "pill_word",
      start: 0.1,
      end: 2.5,
      zone: "lower",
      layer: 1,
      wordRange: [0, 5],
      text: "Making money is a skills problem",
    },
  ],
};

import { StyleGallery, StyleGalleryProps } from "./StyleGallery";
import { StyleShowcase } from "./StyleGallery/Showcase";
import { Still } from "remotion";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition<any, CaptionedVideoProps>
        id="CaptionedVideo"
        component={CaptionedVideo}
        calculateMetadata={calculateCaptionedVideoMetadata}
        defaultProps={{
          timeline: defaultTimeline,
        }}
        width={1080}
        height={1920}
        fps={30}
        durationInFrames={150}
      />

      <Composition<any, StyleGalleryProps>
        id="StyleGallery"
        component={StyleGallery}
        width={1080}
        height={1920}
        fps={30}
        durationInFrames={150}
        defaultProps={{
          styleId: "title3d",
        }}
      />

      <Composition<any, Record<string, unknown>>
        id="StyleShowcase"
        component={StyleShowcase}
        width={1080}
        height={1920}
        fps={30}
        durationInFrames={540} // 9 styles * 60 frames = 18s
      />
    </>
  );
};
