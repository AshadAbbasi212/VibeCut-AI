"""Video Scene Analysis using Vision LLM.

Extracts keyframes from a video, sends them (+ transcript) to a vision-capable
LLM to detect:
  - Scene boundaries and descriptions
  - Speaker positions (for smart crop/reframing)
  - Existing on-screen text / burned-in captions (to skip)
  - Mood / energy level per scene
  - Topic segments (headings, main points)

Supports: Gemini (native video), Mistral Pixtral (keyframes), Anthropic (keyframes).
Falls back gracefully when no vision LLM is available.
"""
import base64
import json
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("scene_analyzer")


# ── Data Models ──────────────────────────────────────────────────────────────

class SceneSpeaker(BaseModel):
    """Detected speaker in a scene."""
    position: str = Field(default="center", description="left, center, right")
    is_speaking: bool = Field(default=False)


class ExistingCaption(BaseModel):
    """Burned-in text already visible on screen."""
    start: float = Field(..., description="Approx start time in seconds")
    end: float = Field(..., description="Approx end time in seconds")
    text: str = Field(default="", description="The visible text on screen")
    region: str = Field(default="lower", description="upper, center, lower")


class TopicSegment(BaseModel):
    """A detected topic/heading segment."""
    start: float = Field(..., description="Segment start time")
    end: float = Field(..., description="Segment end time")
    title: str = Field(default="Main Point", description="Main point / heading text")
    importance: str = Field(default="normal", description="hook, heading, key_point, normal, conclusion")
    energy: str = Field(default="medium", description="low, medium, high, climax")


class SceneInfo(BaseModel):
    """Analysis of a single scene/keyframe."""
    timestamp: float = Field(..., description="Time in seconds")
    description: str = Field(default="", description="Brief scene description")
    speakers: list[SceneSpeaker] = Field(default_factory=list)
    has_existing_text: bool = Field(default=False)
    existing_text: str = Field(default="")
    mood: str = Field(default="neutral", description="excited, calm, serious, funny, dramatic, neutral")
    energy: str = Field(default="medium", description="low, medium, high")


class VideoAnalysis(BaseModel):
    """Complete scene analysis result."""
    scenes: list[SceneInfo] = Field(default_factory=list)
    existing_captions: list[ExistingCaption] = Field(default_factory=list)
    topic_segments: list[TopicSegment] = Field(default_factory=list)
    dominant_mood: str = Field(default="neutral")
    video_type: str = Field(default="talking_head",
                            description="podcast, tutorial, vlog, talking_head, interview, presentation")
    num_speakers: int = Field(default=1)
    has_burned_in_captions: bool = Field(default=False)


# ── Keyframe Extraction ─────────────────────────────────────────────────────

def extract_keyframes(
    video_path: Path,
    output_dir: Path,
    interval_sec: float = 3.0,
    max_frames: int = 40,
    width: int = 512,
) -> list[tuple[float, Path]]:
    """Extract keyframes from video at regular intervals.

    Returns list of (timestamp_sec, frame_path) tuples.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError("ffmpeg not found on PATH")

    # Get video duration first
    ffprobe_bin = shutil.which("ffprobe")
    if ffprobe_bin:
        probe_cmd = [
            ffprobe_bin, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        try:
            duration = float(result.stdout.strip())
        except (ValueError, AttributeError):
            duration = 300.0  # fallback
    else:
        duration = 300.0

    # Calculate timestamps
    timestamps = []
    t = 0.0
    while t < duration and len(timestamps) < max_frames:
        timestamps.append(t)
        t += interval_sec

    if not timestamps:
        timestamps = [0.0]

    frames: list[tuple[float, Path]] = []
    for i, ts in enumerate(timestamps):
        frame_path = output_dir / f"frame_{i:04d}.jpg"
        cmd = [
            ffmpeg_bin, "-y",
            "-ss", f"{ts:.2f}",
            "-i", str(video_path),
            "-vframes", "1",
            "-vf", f"scale={width}:-1",
            "-q:v", "3",
            str(frame_path),
        ]
        try:
            subprocess.run(
                cmd, check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=10,
            )
            if frame_path.exists() and frame_path.stat().st_size > 0:
                frames.append((ts, frame_path))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.warning(f"Failed to extract frame at {ts:.1f}s: {e}")

    logger.info(f"Extracted {len(frames)} keyframes from {video_path.name}")
    return frames


def _load_frame_base64(frame_path: Path) -> str:
    """Load a frame as base64 string."""
    with open(frame_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ── Vision Analysis Prompts ─────────────────────────────────────────────────

SCENE_ANALYSIS_PROMPT = """You are an expert video editor analyzing keyframes from a video to help design professional captions.

For each keyframe (provided with timestamps), analyze:
1. **Scene description** — what's happening visually
2. **Speaker positions** — where people are (left/center/right), who is speaking
3. **Existing on-screen text** — any burned-in captions, titles, lower-thirds, watermarks already visible
4. **Mood/Energy** — the emotional tone (excited, calm, serious, funny, dramatic, neutral) and energy level (low/medium/high)

Also determine overall:
- **video_type**: one of "podcast", "tutorial", "vlog", "talking_head", "interview", "presentation"
- **num_speakers**: how many distinct people appear
- **has_burned_in_captions**: whether the video already has hardcoded subtitles/captions visible

Return ONLY valid JSON matching this schema:
{{
  "scenes": [
    {{
      "timestamp": <float>,
      "description": "<brief description>",
      "speakers": [{{"position": "left|center|right", "is_speaking": true|false}}],
      "has_existing_text": true|false,
      "existing_text": "<text visible on screen or empty>",
      "mood": "excited|calm|serious|funny|dramatic|neutral",
      "energy": "low|medium|high"
    }}
  ],
  "existing_captions": [
    {{"start": <float>, "end": <float>, "text": "<burned-in text>", "region": "upper|center|lower"}}
  ],
  "video_type": "<type>",
  "num_speakers": <int>,
  "has_burned_in_captions": true|false
}}

Keyframe timestamps: {timestamps}
"""

TOPIC_ANALYSIS_PROMPT = """You are an expert content strategist analyzing a video transcript to identify the structural segments, main points, and headings for professional caption styling.

Your job:
1. **Identify topic segments** — break the transcript into logical sections (intro/hook, main points, transitions, conclusion)
2. **Label importance** — each segment gets: "hook" (first attention-grab), "heading" (section title/main point), "key_point" (important claim/insight), "normal" (regular speech), "conclusion" (wrap-up)
3. **Rate energy** — each segment: "low", "medium", "high", "climax"
4. **Detect headings and main points** — if the speaker announces topics, numbered lists, or key takeaways, mark those as "heading" or "key_point"

The transcript with timestamps:
{transcript_json}

{existing_captions_context}

Return ONLY valid JSON:
{{
  "topic_segments": [
    {{
      "start": <float>,
      "end": <float>,
      "title": "<heading or summary of this segment>",
      "importance": "hook|heading|key_point|normal|conclusion",
      "energy": "low|medium|high|climax"
    }}
  ],
  "dominant_mood": "excited|calm|serious|educational|motivational|neutral"
}}
"""


# ── LLM Vision Analyzers ────────────────────────────────────────────────────

def _analyze_with_mistral(
    frames: list[tuple[float, Path]],
    transcript_phrases: list[dict],
    api_key: str,
    existing_captions_ctx: str = "",
) -> VideoAnalysis:
    """Analyze video using Mistral Pixtral (vision) + mistral-small (topics)."""
    try:
        from mistralai.client import Mistral
    except ImportError:
        from mistralai import Mistral

    client = Mistral(api_key=api_key)
    analysis = VideoAnalysis()

    # 1. Vision analysis with Pixtral (keyframes)
    if frames:
        try:
            # Pixtral allows maximum 8 images per request
            if len(frames) <= 8:
                selected_frames = frames
            else:
                step = len(frames) / 8.0
                selected_frames = [frames[int(i * step)] for i in range(8)]

            content_parts = [
                {"type": "text", "text": SCENE_ANALYSIS_PROMPT.format(
                    timestamps=", ".join(f"{ts:.1f}s" for ts, _ in selected_frames)
                )}
            ]

            for ts, frame_path in selected_frames:
                b64 = _load_frame_base64(frame_path)
                content_parts.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })

            response = client.chat.complete(
                model="pixtral-12b-2409",
                messages=[{"role": "user", "content": content_parts}],
                temperature=0.2,
            )

            scene_text = response.choices[0].message.content or ""
            scene_data = _parse_json_response(scene_text)

            if scene_data:
                analysis.video_type = scene_data.get("video_type", "talking_head")
                analysis.num_speakers = scene_data.get("num_speakers", 1)
                analysis.has_burned_in_captions = scene_data.get("has_burned_in_captions", False)

                for s in scene_data.get("scenes", []):
                    analysis.scenes.append(SceneInfo(**{
                        k: v for k, v in s.items()
                        if k in SceneInfo.model_fields
                    }))

                for ec in scene_data.get("existing_captions", []):
                    analysis.existing_captions.append(ExistingCaption(**{
                        k: v for k, v in ec.items()
                        if k in ExistingCaption.model_fields
                    }))

            logger.info(f"Pixtral scene analysis: {len(analysis.scenes)} scenes, "
                        f"type={analysis.video_type}, speakers={analysis.num_speakers}")
        except Exception as e:
            logger.warning(f"Pixtral vision analysis failed: {e}")

    # 2. Topic analysis with text model (use open-mistral-7b for free tier reliability)
    if transcript_phrases:
        try:
            existing_ctx = ""
            if analysis.has_burned_in_captions and analysis.existing_captions:
                existing_ctx = (
                    "IMPORTANT: The video already has these burned-in captions/titles visible on screen. "
                    "Mark their time ranges so we can SKIP generating captions for those segments:\n"
                    + json.dumps([ec.model_dump() for ec in analysis.existing_captions], indent=2)
                )

            prompt = TOPIC_ANALYSIS_PROMPT.format(
                transcript_json=json.dumps(transcript_phrases[:200], indent=2),
                existing_captions_context=existing_ctx or existing_captions_ctx,
            )

            # Try open-mistral-7b (free tier friendly) with fallback to mistral-small-latest
            topic_text = ""
            for topic_model in ["open-mistral-7b", "mistral-small-latest"]:
                try:
                    response = client.chat.complete(
                        model=topic_model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2,
                    )
                    topic_text = response.choices[0].message.content or ""
                    if topic_text:
                        break
                except Exception as model_err:
                    logger.warning(f"Mistral topic model {topic_model} failed: {model_err}")

            topic_text = response.choices[0].message.content or ""
            topic_data = _parse_json_response(topic_text)

            if topic_data:
                analysis.dominant_mood = topic_data.get("dominant_mood", "neutral")
                for seg in topic_data.get("topic_segments", []):
                    analysis.topic_segments.append(TopicSegment(**{
                        k: v for k, v in seg.items()
                        if k in TopicSegment.model_fields
                    }))

            logger.info(f"Topic analysis: {len(analysis.topic_segments)} segments, "
                        f"mood={analysis.dominant_mood}")
        except Exception as e:
            logger.warning(f"Topic analysis failed: {e}")

    return analysis


def _analyze_with_gemini(
    frames: list[tuple[float, Path]],
    transcript_phrases: list[dict],
    api_key: str,
    video_path: Optional[Path] = None,
    existing_captions_ctx: str = "",
) -> VideoAnalysis:
    """Analyze video using Google Gemini (native video or keyframes)."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    analysis = VideoAnalysis()

    # 1. Vision analysis
    if frames:
        try:
            timestamps_str = ", ".join(f"{ts:.1f}s" for ts, _ in frames)
            prompt_text = SCENE_ANALYSIS_PROMPT.format(timestamps=timestamps_str)

            # Use keyframe images
            parts = [prompt_text]
            selected_frames = frames[:20]
            for ts, frame_path in selected_frames:
                b64 = _load_frame_base64(frame_path)
                parts.append(types.Part.from_bytes(
                    data=base64.b64decode(b64),
                    mime_type="image/jpeg",
                ))

            response = client.models.generate_content(
                model=model,
                contents=parts,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )

            scene_text = response.text or ""
            scene_data = _parse_json_response(scene_text)

            if scene_data:
                analysis.video_type = scene_data.get("video_type", "talking_head")
                analysis.num_speakers = scene_data.get("num_speakers", 1)
                analysis.has_burned_in_captions = scene_data.get("has_burned_in_captions", False)

                for s in scene_data.get("scenes", []):
                    analysis.scenes.append(SceneInfo(**{
                        k: v for k, v in s.items()
                        if k in SceneInfo.model_fields
                    }))

                for ec in scene_data.get("existing_captions", []):
                    analysis.existing_captions.append(ExistingCaption(**{
                        k: v for k, v in ec.items()
                        if k in ExistingCaption.model_fields
                    }))

            logger.info(f"Gemini scene analysis: {len(analysis.scenes)} scenes, "
                        f"type={analysis.video_type}, speakers={analysis.num_speakers}")
        except Exception as e:
            logger.warning(f"Gemini vision analysis failed: {e}")

    # 2. Topic analysis
    if transcript_phrases:
        try:
            existing_ctx = ""
            if analysis.has_burned_in_captions and analysis.existing_captions:
                existing_ctx = (
                    "IMPORTANT: The video already has these burned-in captions/titles visible on screen. "
                    "Mark their time ranges so we can SKIP generating captions for those segments:\n"
                    + json.dumps([ec.model_dump() for ec in analysis.existing_captions], indent=2)
                )

            prompt = TOPIC_ANALYSIS_PROMPT.format(
                transcript_json=json.dumps(transcript_phrases[:200], indent=2),
                existing_captions_context=existing_ctx or existing_captions_ctx,
            )

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )

            topic_text = response.text or ""
            topic_data = _parse_json_response(topic_text)

            if topic_data:
                analysis.dominant_mood = topic_data.get("dominant_mood", "neutral")
                for seg in topic_data.get("topic_segments", []):
                    analysis.topic_segments.append(TopicSegment(**{
                        k: v for k, v in seg.items()
                        if k in TopicSegment.model_fields
                    }))

            logger.info(f"Topic analysis: {len(analysis.topic_segments)} segments")
        except Exception as e:
            logger.warning(f"Gemini topic analysis failed: {e}")

    return analysis


def _analyze_with_anthropic(
    frames: list[tuple[float, Path]],
    transcript_phrases: list[dict],
    api_key: str,
    existing_captions_ctx: str = "",
) -> VideoAnalysis:
    """Analyze video using Anthropic Claude (keyframes as images)."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
    analysis = VideoAnalysis()

    # 1. Vision analysis
    if frames:
        try:
            timestamps_str = ", ".join(f"{ts:.1f}s" for ts, _ in frames)
            content_parts = [
                {"type": "text", "text": SCENE_ANALYSIS_PROMPT.format(timestamps=timestamps_str)}
            ]

            selected_frames = frames[:15]  # Claude has lower image limits
            for ts, frame_path in selected_frames:
                b64 = _load_frame_base64(frame_path)
                content_parts.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": b64,
                    }
                })

            response = client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[{"role": "user", "content": content_parts}],
            )

            scene_text = response.content[0].text if response.content else ""
            scene_data = _parse_json_response(scene_text)

            if scene_data:
                analysis.video_type = scene_data.get("video_type", "talking_head")
                analysis.num_speakers = scene_data.get("num_speakers", 1)
                analysis.has_burned_in_captions = scene_data.get("has_burned_in_captions", False)

                for s in scene_data.get("scenes", []):
                    analysis.scenes.append(SceneInfo(**{
                        k: v for k, v in s.items()
                        if k in SceneInfo.model_fields
                    }))

                for ec in scene_data.get("existing_captions", []):
                    analysis.existing_captions.append(ExistingCaption(**{
                        k: v for k, v in ec.items()
                        if k in ExistingCaption.model_fields
                    }))
        except Exception as e:
            logger.warning(f"Anthropic vision analysis failed: {e}")

    # 2. Topic analysis
    if transcript_phrases:
        try:
            existing_ctx = ""
            if analysis.has_burned_in_captions and analysis.existing_captions:
                existing_ctx = (
                    "IMPORTANT: The video already has these burned-in captions/titles visible on screen. "
                    "Mark their time ranges so we can SKIP generating captions for those segments:\n"
                    + json.dumps([ec.model_dump() for ec in analysis.existing_captions], indent=2)
                )

            prompt = TOPIC_ANALYSIS_PROMPT.format(
                transcript_json=json.dumps(transcript_phrases[:200], indent=2),
                existing_captions_context=existing_ctx or existing_captions_ctx,
            )

            response = client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            topic_text = response.content[0].text if response.content else ""
            topic_data = _parse_json_response(topic_text)

            if topic_data:
                analysis.dominant_mood = topic_data.get("dominant_mood", "neutral")
                for seg in topic_data.get("topic_segments", []):
                    analysis.topic_segments.append(TopicSegment(**{
                        k: v for k, v in seg.items()
                        if k in TopicSegment.model_fields
                    }))
        except Exception as e:
            logger.warning(f"Anthropic topic analysis failed: {e}")

    return analysis


# ── JSON Parsing Helpers ─────────────────────────────────────────────────────

def _parse_json_response(raw_text: str) -> Optional[dict]:
    """Robustly parse JSON from LLM response text."""
    cleaned = raw_text.strip()

    # Strip markdown code blocks
    if "```" in cleaned:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()

    # Find outermost { ... }
    if not cleaned.startswith("{") and not cleaned.startswith("["):
        brace = cleaned.find("{")
        bracket = cleaned.find("[")
        indices = [i for i in [brace, bracket] if i != -1]
        if indices:
            first = min(indices)
            char = cleaned[first]
            closer = "}" if char == "{" else "]"
            last = cleaned.rfind(closer)
            if last > first:
                cleaned = cleaned[first:last + 1]

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse LLM JSON: {e}")
        return None


# ── Main Entry Point ─────────────────────────────────────────────────────────

def analyze_video(
    video_path: Path,
    transcript_phrases: list[dict],
    provider: str = "none",
    api_key: Optional[str] = None,
    keyframes_dir: Optional[Path] = None,
) -> VideoAnalysis:
    """Run full video scene analysis.

    Args:
        video_path: Path to the input video
        transcript_phrases: List of phrase dicts with id, text, start, end
        provider: LLM provider ("mistral", "gemini", "anthropic", "none")
        api_key: API key for the provider
        keyframes_dir: Directory to save extracted keyframes

    Returns:
        VideoAnalysis with scenes, topics, existing captions, etc.
    """
    provider = provider.lower().strip()

    if provider == "none":
        logger.info("No LLM provider configured — returning empty analysis")
        return VideoAnalysis()

    # Resolve API key from param or env
    resolved_key = (api_key or "").strip()
    if not resolved_key:
        env_map = {
            "mistral": "MISTRAL_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
        }
        resolved_key = os.getenv(env_map.get(provider, ""), "").strip()

    if not resolved_key:
        logger.warning(f"No API key for {provider} — returning empty analysis")
        return VideoAnalysis()

    # Extract keyframes
    if keyframes_dir is None:
        keyframes_dir = video_path.parent / "keyframes"

    frames = extract_keyframes(video_path, keyframes_dir)

    # Run provider-specific analysis
    try:
        if provider == "mistral":
            return _analyze_with_mistral(frames, transcript_phrases, resolved_key)
        elif provider == "gemini":
            return _analyze_with_gemini(
                frames, transcript_phrases, resolved_key, video_path=video_path
            )
        elif provider == "anthropic":
            return _analyze_with_anthropic(frames, transcript_phrases, resolved_key)
        else:
            logger.warning(f"Unknown provider '{provider}' for analysis")
            return VideoAnalysis()
    except Exception as e:
        logger.exception(f"Video analysis failed: {e}")
        return VideoAnalysis()
