"""Video probing utility using ffprobe."""
import json
import shutil
import subprocess
from pathlib import Path
from pydantic import BaseModel, Field


class VideoProbe(BaseModel):
    width: int = Field(..., description="Video width in pixels")
    height: int = Field(..., description="Video height in pixels")
    fps: float = Field(..., description="Frames per second")
    duration: float = Field(..., description="Duration in seconds")
    has_audio: bool = Field(..., description="Whether the file contains an audio stream")


def parse_fps(fps_str: str) -> float:
    """Parse fps string like '30/1' or '29.97' or '30000/1001' into float."""
    if not fps_str or fps_str == "0/0":
        return 30.0
    if "/" in fps_str:
        num, den = fps_str.split("/", 1)
        try:
            n = float(num)
            d = float(den)
            return round(n / d, 3) if d != 0 else 30.0
        except ValueError:
            return 30.0
    try:
        return round(float(fps_str), 3)
    except ValueError:
        return 30.0


def probe_video(path: str | Path) -> VideoProbe:
    """Probe video file using ffprobe and return VideoProbe model."""
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ffprobe_bin = shutil.which("ffprobe")
    if not ffprobe_bin:
        raise RuntimeError("ffprobe not found on PATH")

    cmd = [
        ffprobe_bin,
        "-v", "error",
        "-show_entries", "format=duration:stream=index,codec_type,width,height,r_frame_rate,avg_frame_rate,duration",
        "-of", "json",
        str(path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr.strip()}")

    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    format_info = data.get("format", {})

    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    if not video_stream:
        raise ValueError(f"No video stream found in {path}")

    width = int(video_stream.get("width", 1080))
    height = int(video_stream.get("height", 1920))

    fps_val = video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate") or "30/1"
    fps = parse_fps(fps_val)

    duration_str = (
        video_stream.get("duration")
        or format_info.get("duration")
        or "0.0"
    )
    try:
        duration = round(float(duration_str), 3)
    except ValueError:
        duration = 0.0

    return VideoProbe(
        width=width,
        height=height,
        fps=fps,
        duration=duration,
        has_audio=audio_stream is not None,
    )
