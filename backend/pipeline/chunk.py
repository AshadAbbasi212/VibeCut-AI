"""Chunking words into natural spoken phrases with configurable rules."""
import argparse
import json
import re
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

from backend.pipeline.transcribe import Word, Transcript


class Phrase(BaseModel):
    id: str = Field(..., description="Unique phrase identifier e.g. p0")
    text: str = Field(..., description="Full text of the phrase")
    start: float = Field(..., description="Display start time in seconds")
    end: float = Field(..., description="Display end time in seconds (extended into silence if needed)")
    speech_start: float = Field(..., description="Actual start time of spoken speech")
    speech_end: float = Field(..., description="Actual end time of spoken speech")
    word_indices: list[int] = Field(..., description="Indices of words from original transcript")
    words: list[Word] = Field(default_factory=list, description="Word objects within this phrase")


class PhrasesDocument(BaseModel):
    language: str = Field(default="en")
    duration: float = Field(..., description="Overall video/audio duration")
    phrases: list[Phrase] = Field(default_factory=list)


# Configurable chunking constants
DEFAULT_MAX_WORDS = 6
DEFAULT_MAX_TITLE_WORDS = 8
DEFAULT_PAUSE_THRESHOLD = 0.35  # seconds
DEFAULT_MIN_PHRASE_DURATION = 0.6  # seconds
DEFAULT_MAX_CHARS_PER_LINE = 28
SENTENCE_END_PUNCTUATION = {".", "!", "?"}
CLAUSE_PUNCTUATION = {",", ";", ":", "—", "-"}


def has_sentence_punctuation(text: str) -> bool:
    """Check if word ends with sentence punctuation (. ! ?)."""
    return any(text.rstrip().endswith(p) for p in SENTENCE_END_PUNCTUATION)


def has_clause_punctuation(text: str) -> bool:
    """Check if word ends with clause punctuation (, ; : etc)."""
    return any(text.rstrip().endswith(p) for p in CLAUSE_PUNCTUATION)


def partition_words(
    words: list[Word],
    max_words: int = DEFAULT_MAX_WORDS,
) -> list[list[Word]]:
    """
    Subdivide a list of words so each sublist has <= max_words,
    avoiding single-word orphan chunks where possible.
    Prefers splitting on clause punctuation when available.
    """
    n = len(words)
    if n <= max_words:
        return [words]

    # Calculate optimal number of chunks k such that ceil(n / k) <= max_words
    # and no chunk has size 1 (unless n == 1)
    k = (n + max_words - 1) // max_words
    # If the remainder gives an orphan (e.g. 7 words with max 6 -> 6 + 1),
    # ensure minimum chunk size is at least 2 when n >= 4.
    min_chunk_size = 2 if n >= 4 else 1

    chunks: list[list[Word]] = []
    start_idx = 0

    while start_idx < n:
        remaining = n - start_idx
        if remaining <= max_words:
            chunks.append(words[start_idx:])
            break

        # Candidate chunk size targeting balanced distribution
        remaining_chunks = (remaining + max_words - 1) // max_words
        target_size = min(max_words, max(min_chunk_size, remaining // remaining_chunks))

        # Look for clause punctuation around target_size (+/- 1) to make a natural split
        best_size = target_size
        for offset in (0, 1, -1):
            cand = target_size + offset
            if min_chunk_size <= cand <= max_words and (remaining - cand) >= min_chunk_size:
                cand_word = words[start_idx + cand - 1]
                if has_clause_punctuation(cand_word.text):
                    best_size = cand
                    break

        # Ensure we never leave a single-word orphan in the remaining words
        if remaining - best_size == 1:
            if best_size > min_chunk_size:
                best_size -= 1
            else:
                best_size += 1

        chunks.append(words[start_idx : start_idx + best_size])
        start_idx += best_size

    return chunks


def chunk_words(
    words: list[Word],
    duration: float = 0.0,
    max_words: int = DEFAULT_MAX_WORDS,
    pause_threshold: float = DEFAULT_PAUSE_THRESHOLD,
    min_phrase_duration: float = DEFAULT_MIN_PHRASE_DURATION,
) -> list[Phrase]:
    """
    Chunk a sequence of words into phrases adhering to:
    - break on pause > pause_threshold
    - break after sentence punctuation
    - max max_words per phrase
    - avoid single-word orphans where possible
    - min min_phrase_duration (extended into following silence, never into next phrase speech)
    - no overlap between phrase speech or display ranges
    """
    if not words:
        return []

    # Step 1: Split on primary boundaries (sentence punctuation and pauses)
    segments: list[list[Word]] = []
    current_segment: list[Word] = [words[0]]

    for i in range(1, len(words)):
        prev_w = words[i - 1]
        curr_w = words[i]

        pause = curr_w.start - prev_w.end
        is_pause_break = pause > pause_threshold
        is_punct_break = has_sentence_punctuation(prev_w.text)

        if is_pause_break or is_punct_break:
            segments.append(current_segment)
            current_segment = [curr_w]
        else:
            current_segment.append(curr_w)

    if current_segment:
        segments.append(current_segment)

    # Step 2: Subdivide segments exceeding max_words
    word_groups: list[list[Word]] = []
    for seg in segments:
        sub_chunks = partition_words(seg, max_words=max_words)
        word_groups.extend(sub_chunks)

    # Step 3: Construct Phrase objects with safe timing extensions
    phrases: list[Phrase] = []
    for idx, group in enumerate(word_groups):
        speech_start = group[0].start
        speech_end = group[-1].end
        phrase_text = " ".join(w.text for w in group)
        word_indices = [w.i for w in group]

        phrases.append(
            Phrase(
                id=f"p{idx}",
                text=phrase_text,
                start=round(speech_start, 3),
                end=round(speech_end, 3),
                speech_start=round(speech_start, 3),
                speech_end=round(speech_end, 3),
                word_indices=word_indices,
                words=group,
            )
        )

    # Step 4: Adjust display timings (min duration into silence, strictly no overlap)
    total_phrases = len(phrases)
    for i in range(total_phrases):
        p = phrases[i]
        curr_duration = p.end - p.start

        # Determine upper boundary: next phrase speech_start or total video duration
        if i + 1 < total_phrases:
            limit_end = phrases[i + 1].speech_start
        else:
            limit_end = max(duration, p.speech_end)

        if curr_duration < min_phrase_duration:
            needed = min_phrase_duration - curr_duration
            potential_end = p.speech_end + needed
            # Extend into silence up to limit_end (with a 0.02s safety margin if next phrase exists)
            safe_limit = limit_end - 0.02 if i + 1 < total_phrases else limit_end
            p.end = round(min(potential_end, max(p.speech_end, safe_limit)), 3)

        # Enforce invariant: phrase end <= next phrase start
        if i + 1 < total_phrases and p.end > phrases[i + 1].start:
            p.end = phrases[i + 1].start

    return phrases


def chunk_transcript(
    transcript: Transcript,
    max_words: int = DEFAULT_MAX_WORDS,
    pause_threshold: float = DEFAULT_PAUSE_THRESHOLD,
    min_phrase_duration: float = DEFAULT_MIN_PHRASE_DURATION,
) -> PhrasesDocument:
    """Chunk a full Transcript into PhrasesDocument."""
    phrases = chunk_words(
        words=transcript.words,
        duration=transcript.duration,
        max_words=max_words,
        pause_threshold=pause_threshold,
        min_phrase_duration=min_phrase_duration,
    )
    return PhrasesDocument(
        language=transcript.language,
        duration=transcript.duration,
        phrases=phrases,
    )


def main():
    ap = argparse.ArgumentParser(description="Chunk transcribed words into natural phrases.")
    ap.add_argument("input", help="Path to words.json")
    ap.add_argument("-o", "--output", default="out/phrases.json", help="Path to phrases.json")
    ap.add_argument("--max-words", type=int, default=DEFAULT_MAX_WORDS, help="Maximum words per phrase")
    ap.add_argument("--pause", type=float, default=DEFAULT_PAUSE_THRESHOLD, help="Pause threshold in seconds")
    ap.add_argument("--min-duration", type=float, default=DEFAULT_MIN_PHRASE_DURATION, help="Minimum phrase duration")
    args = ap.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    data = json.loads(input_path.read_text(encoding="utf-8"))
    transcript = Transcript.model_validate(data)

    doc = chunk_transcript(
        transcript=transcript,
        max_words=args.max_words,
        pause_threshold=args.pause,
        min_phrase_duration=args.min_duration,
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(doc.model_dump_json(indent=2), encoding="utf-8")
    print(f"Chunked {len(transcript.words)} words into {len(doc.phrases)} phrases -> {out_path}")


if __name__ == "__main__":
    main()
