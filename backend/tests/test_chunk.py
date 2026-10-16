"""Tests for chunking words into phrases."""
import json
from pathlib import Path
import pytest
from backend.pipeline.transcribe import Word
from backend.pipeline.chunk import (
    chunk_words,
    partition_words,
    PhrasesDocument,
    has_sentence_punctuation,
    DEFAULT_MAX_WORDS,
)


def make_word(i: int, text: str, start: float, end: float) -> Word:
    return Word(i=i, text=text, start=round(start, 3), end=round(end, 3), prob=1.0)


def test_pause_break():
    # Gap between word 1 and 2 is 0.5s (> 0.35s)
    words = [
        make_word(0, "First", 0.0, 0.4),
        make_word(1, "part", 0.4, 0.8),
        make_word(2, "Second", 1.3, 1.7),  # 1.3 - 0.8 = 0.5s pause
        make_word(3, "part", 1.7, 2.0),
    ]
    phrases = chunk_words(words, duration=3.0, pause_threshold=0.35)
    assert len(phrases) == 2
    assert phrases[0].text == "First part"
    assert phrases[1].text == "Second part"
    assert phrases[0].end <= phrases[1].start


def test_punctuation_break():
    words = [
        make_word(0, "Hello.", 0.0, 0.4),  # ends with period
        make_word(1, "How", 0.45, 0.7),
        make_word(2, "are", 0.7, 0.9),
        make_word(3, "you?", 0.9, 1.2),    # ends with question mark
        make_word(4, "Fine!", 1.25, 1.5),  # ends with exclamation mark
    ]
    phrases = chunk_words(words, duration=2.0)
    assert len(phrases) == 3
    assert phrases[0].text == "Hello."
    assert phrases[1].text == "How are you?"
    assert phrases[2].text == "Fine!"


def test_max_words_and_orphan_avoidance():
    # 7 words: should be partitioned into 4 and 3 or 3 and 4, never 6 and 1
    words = [
        make_word(i, f"word{i}", i * 0.3, i * 0.3 + 0.25)
        for i in range(7)
    ]
    phrases = chunk_words(words, max_words=6)
    assert len(phrases) == 2
    chunk_lengths = [len(p.words) for p in phrases]
    assert 1 not in chunk_lengths, f"Single-word orphan detected: {chunk_lengths}"
    assert all(length <= 6 for length in chunk_lengths)


def test_partition_words_balance():
    # Test partition with 8, 9, 11 words
    for n in (7, 8, 9, 10, 11, 13):
        words = [make_word(i, f"w{i}", i * 0.2, i * 0.2 + 0.18) for i in range(n)]
        groups = partition_words(words, max_words=6)
        lengths = [len(g) for g in groups]
        assert all(l <= 6 for l in lengths)
        assert 1 not in lengths, f"Orphan found for n={n}: {lengths}"


def test_no_overlap_between_phrases():
    words = [
        make_word(0, "Short", 0.1, 0.3),  # duration 0.2s (< 0.6s min)
        make_word(1, "Second", 0.5, 0.9), # pause is 0.2s (< 0.35s)
        make_word(2, "Third", 1.5, 1.9),
    ]
    phrases = chunk_words(words, duration=3.0, min_phrase_duration=0.6)
    for i in range(len(phrases) - 1):
        assert phrases[i].end <= phrases[i + 1].start, (
            f"Overlap detected: phrase {i} end {phrases[i].end} > next start {phrases[i+1].start}"
        )
        assert phrases[i].speech_end <= phrases[i + 1].speech_start


def test_real_phrases_json():
    phrases_path = Path("out/phrases.json")
    if not phrases_path.exists():
        pytest.skip("out/phrases.json not generated yet")

    data = json.loads(phrases_path.read_text(encoding="utf-8"))
    doc = PhrasesDocument.model_validate(data)
    assert len(doc.phrases) > 0

    for i, p in enumerate(doc.phrases):
        assert len(p.words) <= DEFAULT_MAX_WORDS
        assert p.start < p.end
        assert p.speech_start <= p.speech_end
        assert len(p.word_indices) == len(p.words)
        if i + 1 < len(doc.phrases):
            next_p = doc.phrases[i + 1]
            assert p.end <= next_p.start
            assert p.speech_end <= next_p.speech_start
