"""Pipeline module to render Remotion compositions to MP4."""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Callable

from backend.schemas.timeline import Timeline
from backend.pipeline.probe import probe_video


def get_remotion_dir() -> Path:
    """Return the absolute path to the remotion directory."""
    root = Path(__file__).resolve().parent.parent.parent
    return root / "remotion"


def resolve_npx() -> str:
    """Find npx executable across platforms (npx.cmd on Windows)."""
    if sys.platform == "win32":
        bin_path = shutil.which("npx.cmd") or shutil.which("npx")
    else:
        bin_path = shutil.which("npx")
    if not bin_path:
        raise RuntimeError("npx not found on PATH. Node.js must be installed.")
    return bin_path


def prepare_video_asset(video_path: Path, job_id: str = "default") -> str:
    """
    Ensure video file is accessible to Remotion via public/jobs/<job_id>/input.mp4.
    Returns relative public path string suitable for staticFile().
    """
    remotion_dir = get_remotion_dir()
    public_job_dir = remotion_dir / "public" / "jobs" / job_id
    public_job_dir.mkdir(parents=True, exist_ok=True)
    target_file = public_job_dir / "input.mp4"

    video_resolved = video_path.resolve()
    target_resolved = target_file.resolve()

    if video_resolved != target_resolved:
        # Copy or update file
        if not target_file.exists() or target_file.stat().st_size != video_resolved.stat().st_size:
            shutil.copy2(video_resolved, target_file)

    return f"jobs/{job_id}/input.mp4"


def render(
    timeline_input: Timeline | str | Path,
    output_path: str | Path,
    frames: Optional[str] = None,
    concurrency: Optional[int] = None,
    scale: Optional[float] = None,
    draft: bool = False,
    progress_callback: Optional[Callable[[float], None]] = None,
) -> Path:
    """
    Render CaptionedVideo composition using Remotion CLI.
    
    Args:
        timeline_input: Timeline model instance or path to timeline.json
        output_path: Target .mp4 file destination
        frames: Optional frame range string like '0-150'
        concurrency: Number of render threads
        scale: Scaling factor (e.g. 0.5 for half resolution)
        draft: Convenience flag to render at scale 0.5 for fast previews
        progress_callback: Optional callable receiving progress (0.0 to 1.0)
    
    Returns:
        Path to rendered MP4 file
    """
    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    remotion_dir = get_remotion_dir()
    npx_bin = resolve_npx()

    # Determine timeline model
    if isinstance(timeline_input, Timeline):
        timeline = timeline_input
    else:
        timeline_path = Path(timeline_input).resolve()
        if not timeline_path.exists():
            raise FileNotFoundError(f"Timeline file not found: {timeline_path}")
        timeline_data = json.loads(timeline_path.read_text(encoding="utf-8"))
        timeline = Timeline.model_validate(timeline_data)

    # Ensure video asset is accessible in remotion/public
    if not (timeline.video.src.startswith("http://") or timeline.video.src.startswith("https://")):
        remotion_public = remotion_dir / "public"
        if not (remotion_public / timeline.video.src).exists():
            candidate = Path(timeline.video.src)
            if not candidate.is_absolute():
                candidate = Path.cwd() / candidate
            if candidate.exists():
                public_rel = prepare_video_asset(candidate)
                timeline = timeline.model_copy(
                    update={"video": timeline.video.model_copy(update={"src": public_rel})}
                )

    # Standardize props structure so both props.timeline and props.<field> exist
    props_payload = {
        "timeline": timeline.model_dump(),
        **timeline.model_dump(),
    }
    props_file = remotion_dir / "public" / "temp" / "render_props.json"
    props_file.parent.mkdir(parents=True, exist_ok=True)
    props_file.write_text(json.dumps(props_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    cmd = [
        npx_bin,
        "remotion",
        "render",
        "CaptionedVideo",
        str(out_file),
        "--props=./public/temp/render_props.json",
    ]

    if draft and scale is None:
        scale = 0.5

    if frames:
        cmd.append(f"--frames={frames}")
    if concurrency:
        cmd.append(f"--concurrency={concurrency}")
    if scale:
        cmd.append(f"--scale={scale}")

    # Remotion render command executed in remotion directory
    process = subprocess.Popen(
        cmd,
        cwd=str(remotion_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    logs = []
    for line in iter(process.stdout.readline, ""):
        line_clean = line.strip()
        if not line_clean:
            continue
        logs.append(line_clean)
        # Check for progress percentage in output
        if "%" in line_clean and progress_callback:
            try:
                import re
                match = re.search(r"(\d+)%", line_clean)
                if match:
                    pct = int(match.group(1)) / 100.0
                    progress_callback(pct)
            except Exception:
                pass

    process.stdout.close()
    return_code = process.wait()

    if return_code != 0:
        error_msg = "\n".join(logs[-25:])
        raise RuntimeError(f"Remotion render failed with exit code {return_code}:\n{error_msg}")

    if not out_file.exists() or out_file.stat().st_size == 0:
        raise RuntimeError(f"Remotion render produced empty or missing file at {out_file}")

    return out_file


def main():
    ap = argparse.ArgumentParser(description="Render timeline.json to video.")
    ap.add_argument("timeline", help="Path to timeline.json")
    ap.add_argument("-o", "--output", default="out/output.mp4", help="Path to output MP4")
    ap.add_argument("--frames", default=None, help="Frame range to render (e.g. 0-150)")
    ap.add_argument("--concurrency", type=int, default=None, help="Number of worker threads")
    ap.add_argument("--scale", type=float, default=None, help="Scale factor (e.g. 0.5 for draft)")
    ap.add_argument("--draft", action="store_true", help="Render at half-resolution (scale 0.5)")
    args = ap.parse_args()

    out_path = render(
        timeline_input=args.timeline,
        output_path=args.output,
        frames=args.frames,
        concurrency=args.concurrency,
        scale=args.scale,
        draft=args.draft,
    )
    print(f"Render complete -> {out_path}")


if __name__ == "__main__":
    main()
