"""Tests for transcription and video probing."""
import json
import pytest
from pathlib import Path
from backend.pipeline.probe import probe_video, parse_fps
from backend.pipeline.transcribe import (
    Word,
    Transcript,
    sanitize_word_timestamps,
)


def test_parse_fps():
    assert parse_fps("30/1") == 30.0
    assert parse_fps("60/2") == 30.0
    assert parse_fps("29.97") == 29.97
    assert parse_fps("invalid") == 30.0


def test_sanitize_word_timestamps_invariants():
    # Raw words with disordered timestamps and overlaps
    raw = [
        {"text": "Hello", "start": 1.0, "end": 0.8},  # end < start
        {"text": "world", "start": 0.5, "end": 1.2},  # start < previous end
        {"text": "", "start": 1.3, "end": 1.4},        # empty text should be ignored
        {"text": "again", "start": 1.5, "end": 2.0},
    ]

    cleaned = sanitize_word_timestamps(raw)
    assert len(cleaned) == 3

    # Check invariants
    for i, w in enumerate(cleaned):
        assert w.i == i
        assert w.start < w.end
        assert len(w.text) > 0
        if i > 0:
            assert w.start >= cleaned[i - 1].end


def test_transcript_model_validation():
    fixture = {
        "language": "en",
        "duration": 5.0,
        "words": [
            {"i": 0, "text": "Making", "start": 0.1, "end": 0.5, "prob": 0.98},
            {"i": 1, "text": "money", "start": 0.5, "end": 0.9, "prob": 0.99},
        ],
    }
    transcript = Transcript.model_validate(fixture)
    assert transcript.language == "en"
    assert len(transcript.words) == 2
    assert transcript.words[0].text == "Making"
    assert transcript.words[1].end == 0.9


def test_probe_synthetic():
    sample_path = Path("samples/synthetic.mp4")
    if not sample_path.exists():
        pytest.skip("samples/synthetic.mp4 not present")

    probe = probe_video(sample_path)
    assert probe.width == 1080
    assert probe.height == 1920
    assert probe.fps == 30.0
    assert probe.duration > 0
    assert probe.has_audio is True


def test_out_words_json_monotonic():
    words_path = Path("out/words.json")
    if not words_path.exists():
        pytest.skip("out/words.json not present")

    data = json.loads(words_path.read_text(encoding="utf-8"))
    transcript = Transcript.model_validate(data)
    assert len(transcript.words) > 0

    last_start = -1.0
    for w in transcript.words:
        assert w.start < w.end
        assert w.start >= last_start
        last_start = w.start


def test_compute_fast_file_hash_consistency(tmp_path):
    from backend.pipeline.transcribe import compute_fast_file_hash, compute_file_sha256
    # Test small file
    small_file = tmp_path / "small.mp4"
    small_file.write_bytes(b"hello world test content 12345")
    assert compute_fast_file_hash(small_file) == compute_file_sha256(small_file)

    # Test large file (> 4MB) sampling
    large_file = tmp_path / "large.mp4"
    large_file.write_bytes(b"A" * (5 * 1024 * 1024))
    h1 = compute_fast_file_hash(large_file)
    h2 = compute_fast_file_hash(large_file)
    assert h1 == h2
    assert isinstance(h1, str)
    assert len(h1) == 64


def test_extract_audio_wav_fallback(tmp_path):
    from backend.pipeline.transcribe import extract_audio_wav
    fake_file = tmp_path / "non_existent.mp4"
    out_wav = tmp_path / "out.wav"
    assert extract_audio_wav(fake_file, out_wav) is False

