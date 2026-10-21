"""Tests for style library, registry, gallery stills, and showcase render."""
from pathlib import Path
import pytest
from backend.schemas.timeline import VALID_STYLES
from backend.pipeline.probe import probe_video


REQUIRED_STYLES = [
    "title3d",
    "blob_card",
    "pill_word",
    "serif_title",
    "numbered_point",
    "handwritten",
    "arc_letters",
    "sticker",
]


def test_styles_in_schema():
    for style in REQUIRED_STYLES:
        assert style in VALID_STYLES, f"Style '{style}' missing from VALID_STYLES"


def test_all_24_styles_in_schema():
    all_24 = [
        "title3d", "blob_card", "pill_word", "serif_title", "numbered_point",
        "handwritten", "arc_letters", "sticker", "neon_glow", "typewriter_terminal",
        "paper_cutout", "glitch_kinetic", "quote_editorial", "comic_bubble",
        "gradient_outline", "minimal_underline", "hormozi_bold", "retro_vaporwave",
        "karaoke_bounce", "fire_burn", "beast_impact", "highlighter_marker",
        "cinematic_minimal", "cyber_hud"
    ]
    assert len(all_24) == 24
    for s in all_24:
        assert s in VALID_STYLES, f"Style '{s}' missing from VALID_STYLES"


def test_gallery_stills_exist():
    gallery_dir = Path("out/gallery")
    if not gallery_dir.exists():
        pytest.skip("out/gallery directory not generated yet")

    for style in REQUIRED_STYLES:
        still_file = gallery_dir / f"{style}.png"
        assert still_file.exists(), f"Gallery still missing for '{style}': {still_file}"
        assert still_file.stat().st_size > 1000, f"Gallery still too small: {still_file}"


def test_comparison_images_exist():
    compare_dir = Path("out/gallery/compare")
    if not compare_dir.exists():
        pytest.skip("out/gallery/compare directory not generated yet")

    for style in REQUIRED_STYLES:
        compare_file = compare_dir / f"{style}_compare.png"
        assert compare_file.exists(), f"Comparison image missing for '{style}': {compare_file}"
        assert compare_file.stat().st_size > 1000, f"Comparison image too small: {compare_file}"


def test_showcase_video():
    showcase_file = Path("out/gallery/showcase.mp4")
    if not showcase_file.exists():
        pytest.skip("out/gallery/showcase.mp4 not generated yet")

    probe = probe_video(showcase_file)
    assert probe.width == 1080
    assert probe.height == 1920
    assert probe.fps == 30.0
    assert probe.duration >= 17.5  # 9 styles * 2s
