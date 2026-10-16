"""Generate gallery stills for all caption styles and create side-by-side comparisons."""
import json
import shutil
import subprocess
import sys
from pathlib import Path
from backend.pipeline.render import resolve_npx, get_remotion_dir


STYLES_CONFIG = [
    {
        "id": "title3d",
        "props": {"styleId": "title3d", "palette": "sunset"},
        "ref": "docs/reference-screenshots/01-title3d-gradient-extruded.png",
    },
    {
        "id": "blob_card",
        "props": {"styleId": "blob_card", "variant": "glow"},
        "ref": "docs/reference-screenshots/02-blob-card-glow-serif.png",
    },
    {
        "id": "blob_card_frosted",
        "props": {"styleId": "blob_card", "variant": "frosted"},
        "ref": "docs/reference-screenshots/07-frosted-blob-red-emphasis.png",
    },
    {
        "id": "pill_word",
        "props": {"styleId": "pill_word"},
        "ref": "docs/reference-screenshots/03-pill-word-by-word.png",
    },
    {
        "id": "serif_title",
        "props": {"styleId": "serif_title"},
        "ref": "docs/reference-screenshots/05-serif-title-keyword-pill-ellipse-doodle.png",
    },
    {
        "id": "numbered_point",
        "props": {"styleId": "numbered_point"},
        "ref": "docs/reference-screenshots/06-numbered-point-italic-highlight.png",
    },
    {
        "id": "handwritten",
        "props": {"styleId": "handwritten"},
        "ref": "docs/reference-screenshots/04-handwritten-arc-letters-sticker-pill.png",
    },
    {
        "id": "arc_letters",
        "props": {"styleId": "arc_letters"},
        "ref": "docs/reference-screenshots/04-handwritten-arc-letters-sticker-pill.png",
    },
    {
        "id": "sticker",
        "props": {"styleId": "sticker"},
        "ref": "docs/reference-screenshots/04-handwritten-arc-letters-sticker-pill.png",
    },
]


def render_style_still(style_info: dict, out_dir: Path) -> Path:
    remotion_dir = get_remotion_dir()
    npx_bin = resolve_npx()
    style_id = style_info["id"]

    out_file = (out_dir / f"{style_id}.png").resolve()

    # Write props to temp file
    temp_props = remotion_dir / "public" / "temp" / f"gallery_{style_id}.json"
    temp_props.parent.mkdir(parents=True, exist_ok=True)
    temp_props.write_text(json.dumps(style_info["props"], indent=2), encoding="utf-8")

    cmd = [
        npx_bin,
        "remotion",
        "still",
        "StyleGallery",
        str(out_file),
        "--frame=25",
        f"--props=./public/temp/gallery_{style_id}.json",
    ]

    print(f"Rendering still for '{style_id}' -> {out_file.name}...")
    subprocess.run(cmd, cwd=str(remotion_dir), check=True)
    return out_file


def create_comparison(rendered_png: Path, ref_png: Path, compare_out: Path):
    """Create side-by-side comparison image using ffmpeg hstack."""
    compare_out.parent.mkdir(parents=True, exist_ok=True)
    # Scale both to 540x960 and stack horizontally with labels
    filter_complex = (
        "[0:v]scale=540:960,drawtext=text='Target Reference':fontcolor=white:fontsize=28:x=20:y=20:box=1:boxcolor=black@0.6[left];"
        "[1:v]scale=540:960,drawtext=text='Rendered Style':fontcolor=white:fontsize=28:x=20:y=20:box=1:boxcolor=black@0.6[right];"
        "[left][right]hstack=inputs=2[out]"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(ref_png),
        "-i", str(rendered_png),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        str(compare_out),
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def main():
    root = Path(__file__).resolve().parent.parent
    out_gallery = root / "out" / "gallery"
    out_compare = out_gallery / "compare"
    out_gallery.mkdir(parents=True, exist_ok=True)
    out_compare.mkdir(parents=True, exist_ok=True)

    for item in STYLES_CONFIG:
        still_file = render_style_still(item, out_gallery)
        ref_file = root / item["ref"]
        if ref_file.exists():
            compare_file = out_compare / f"{item['id']}_compare.png"
            create_comparison(still_file, ref_file, compare_file)
            print(f"  Comparison saved -> {compare_file.name}")

    # Also render the 18-second showcase video (2s per style)
    remotion_dir = get_remotion_dir()
    npx_bin = resolve_npx()
    showcase_out = (out_gallery / "showcase.mp4").resolve()
    print(f"\nRendering StyleShowcase video (plays 2s of each style) -> {showcase_out.name}...")
    cmd_showcase = [
        npx_bin,
        "remotion",
        "render",
        "StyleShowcase",
        str(showcase_out),
    ]
    subprocess.run(cmd_showcase, cwd=str(remotion_dir), check=True)
    print(f"All gallery stills and showcase video generated successfully!")


if __name__ == "__main__":
    main()
