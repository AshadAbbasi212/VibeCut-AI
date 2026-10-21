"""Pydantic schema for timeline.json - single source of truth between Python and Remotion."""
from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator


VALID_STYLES = {
    "title3d",
    "blob_card",
    "pill_word",
    "serif_title",
    "numbered_point",
    "handwritten",
    "arc_letters",
    "sticker",
    "neon_glow",
    "typewriter_terminal",
    "paper_cutout",
    "glitch_kinetic",
    "quote_editorial",
    "comic_bubble",
    "gradient_outline",
    "minimal_underline",
    "hormozi_bold",
    "retro_vaporwave",
    "karaoke_bounce",
    "fire_burn",
}

VALID_ZONES = {"upper", "center", "lower", "free"}
VALID_HIGHLIGHT_KINDS = {"color", "italic", "pill", "underline", "scale"}
VALID_DECORATIONS = {"sparkles", "ellipse", "underline_scribble", "arrow", "none"}
VALID_GRAPHIC_KINDS = {"emoji", "icon", "image"}


class CameraCut(BaseModel):
    start: float = Field(..., description="Cut start time in seconds")
    end: float = Field(..., description="Cut end time in seconds")
    focusX: float = Field(default=0.5, description="Horizontal center focus (0.0 to 1.0)")
    speakerId: Optional[str] = Field(default="speaker_0", description="Identifier of the active speaker")
    layout: Optional[Literal["solo", "split_duo", "split_trio", "wide"]] = Field(
        default="solo", description="Layout mode for this cut segment"
    )


class TimelineVideo(BaseModel):
    src: str = Field(..., description="Path or relative URL to the video source")
    width: int = Field(default=1080, description="Video width in pixels")
    height: int = Field(default=1920, description="Video height in pixels")
    fps: float = Field(default=30.0, description="Frames per second")
    durationSec: float = Field(..., description="Total duration in seconds")
    layout: Optional[Literal["split_podcast", "split_triple", "blur_fit", "fill", "focus_left", "focus_right", "active_speaker"]] = Field(
        default="split_podcast", description="Video framing layout for landscape to vertical conversion"
    )
    originalWidth: Optional[int] = Field(default=None, description="Original source video width")
    originalHeight: Optional[int] = Field(default=None, description="Original source video height")


class TimelineWord(BaseModel):
    i: int = Field(..., description="Global word index")
    text: str = Field(..., description="Word text")
    start: float = Field(..., description="Word start time in seconds")
    end: float = Field(..., description="Word end time in seconds")


class Highlight(BaseModel):
    wordIndex: int = Field(..., description="Index of word to highlight")
    kind: Literal["color", "italic", "pill", "underline", "scale"] = Field(
        default="color", description="Highlight treatment"
    )
    value: str = Field(..., description="Color code or token")


class Graphic(BaseModel):
    kind: Literal["emoji", "icon", "image"] = Field(..., description="Type of graphic")
    value: str = Field(..., description="Emoji char, Lucide icon name, or image path")
    position: Optional[Literal["above", "below", "left", "right"]] = Field(
        default="above", description="Placement relative to text"
    )


class AnimationConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    in_: Optional[Literal["pop", "slide_up", "fade", "typewriter", "none"]] = Field(
        default="pop", alias="in"
    )
    out: Optional[Literal["fade", "pop", "none"]] = Field(default="fade")
    wordStagger: Optional[float] = Field(default=0.04)


class TimelineEvent(BaseModel):
    id: str = Field(..., description="Unique event id e.g. e1")
    style: str = Field(..., description="Style identifier from docs/04")
    start: float = Field(..., description="Event start in seconds")
    end: float = Field(..., description="Event end in seconds")
    zone: Literal["upper", "center", "lower", "free"] = Field(default="lower")
    x: Optional[float] = Field(default=None, description="Fractional x (0-1) for free zone")
    y: Optional[float] = Field(default=None, description="Fractional y (0-1) for free zone")
    layer: int = Field(default=1, description="Z-order layer (higher on top)")
    wordRange: list[int] = Field(default_factory=list, description="[firstIndex, lastIndex] inclusive")
    text: str = Field(..., description="Spoken text in this event")
    lines: Optional[list[str]] = Field(default=None, description="Pre-split lines for multi-line layout")
    highlights: Optional[list[Highlight]] = Field(default=None)
    palette: Optional[str] = Field(default="sunset")
    decorations: Optional[list[str]] = Field(default=None)
    graphic: Optional[Graphic] = Field(default=None)
    animation: Optional[AnimationConfig] = Field(default=None)
    variant: Optional[str] = Field(default=None, description="Optional style variant e.g. 'glow' or 'frosted'")
    captionSize: Optional[str] = Field(
        default=None, description="Optional caption size override (small, medium, large, or custom px)"
    )
    backgroundStyle: Optional[Literal["transparent", "glass", "solid"]] = Field(
        default=None, description="Caption background style: transparent, glass, solid"
    )
    highlightColor: Optional[str] = Field(
        default=None, description="Word highlight hex color"
    )
    sentenceId: Optional[str] = Field(
        default=None, description="Grouping identifier for sentence-level style consistency"
    )

    @model_validator(mode="after")
    def validate_event(self) -> "TimelineEvent":
        if self.style not in VALID_STYLES:
            raise ValueError(f"Unknown style '{self.style}'. Must be one of {VALID_STYLES}")
        if self.end <= self.start:
            raise ValueError(f"Event {self.id}: end ({self.end}) must be greater than start ({self.start})")
        if self.end - self.start < 0.3:
            raise ValueError(f"Event {self.id}: duration ({self.end - self.start:.2f}s) too short (< 0.3s)")
        return self


class Timeline(BaseModel):
    version: int = Field(default=1)
    video: TimelineVideo
    language: str = Field(default="en")
    words: list[TimelineWord] = Field(default_factory=list)
    events: list[TimelineEvent] = Field(default_factory=list)
    captionSize: Optional[str] = Field(
        default="medium", description="Global caption size (small, medium, large, or custom px)"
    )
    backgroundStyle: Optional[Literal["transparent", "glass", "solid"]] = Field(
        default="transparent", description="Global background style"
    )
    highlightColor: Optional[str] = Field(
        default="#38BDF8", description="Global highlight color"
    )
    subtitleY: Optional[float] = Field(
        default=None, description="Global custom Y position (0.0 to 1.0) dragged by user"
    )
    videoLayout: Optional[Literal["split_podcast", "split_triple", "blur_fit", "fill", "focus_left", "focus_right", "active_speaker"]] = Field(
        default="split_podcast", description="Video framing layout for landscape to vertical conversion"
    )
    cameraCuts: Optional[list[CameraCut]] = Field(
        default=None, description="Dynamic camera cut timeline for active speaker tracking"
    )

    @model_validator(mode="after")
    def validate_timeline_invariants(self) -> "Timeline":
        # 1. 0 <= start < end <= video.durationSec (with slight tolerance for rounding)
        max_duration = self.video.durationSec + 0.1
        for e in self.events:
            if e.start < 0:
                raise ValueError(f"Event {e.id} starts before 0: {e.start}")
            if e.end > max_duration:
                raise ValueError(f"Event {e.id} ends ({e.end}) after video duration ({self.video.durationSec})")

        # 2. Check words are non-decreasing
        last_t = -1.0
        for w in self.words:
            if w.start < last_t:
                raise ValueError(f"Words not sorted: word {w.i} ({w.text}) starts at {w.start} < {last_t}")
            last_t = w.start

        # 3. Concurrency check: max 3 events overlap simultaneously; no same zone overlaps
        # Sample points at start of each event + midpoint
        time_points = set()
        for e in self.events:
            time_points.add(e.start + 0.01)
            time_points.add((e.start + e.end) / 2.0)
            time_points.add(max(0.0, e.end - 0.01))

        for t in sorted(time_points):
            active = [e for e in self.events if e.start <= t < e.end]
            if len(active) > 3:
                raise ValueError(f"More than 3 concurrent events at t={t:.2f}s: {[e.id for e in active]}")

            # Zone collision check: no two events in the same zone at time t
            # (unless free zone with distinct coordinates)
            zones = [e.zone for e in active if e.zone != "free"]
            if len(zones) != len(set(zones)):
                raise ValueError(f"Zone collision at t={t:.2f}s: multiple events in {zones}")

        return self


def export_json_schema(output_path: str = "backend/schemas/timeline_schema.json") -> str:
    """Export Pydantic Timeline schema as JSON Schema file."""
    import json
    from pathlib import Path

    schema_dict = Timeline.model_json_schema()
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(schema_dict, f, indent=2)
    return str(out)


if __name__ == "__main__":
    export_json_schema()
