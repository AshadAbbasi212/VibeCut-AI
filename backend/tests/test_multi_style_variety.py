import json
import pytest
from backend.pipeline.chunk import Phrase
from backend.pipeline.transcribe import Word
from backend.pipeline.plan_llm import _validate_and_parse_llm_json
from backend.pipeline.plan_rules import RulePlanner
from backend.pipeline.clips import slice_timeline_for_clip
from backend.schemas.timeline import Timeline, TimelineEvent


def test_rule_planner_multi_style_variety_toggle():
    """Verify RulePlanner respects multi_style_variety boolean toggle."""
    words = [
        Word(i=0, text="Welcome", start=0.0, end=0.4, probability=0.99),
        Word(i=1, text="to", start=0.4, end=0.6, probability=0.99),
        Word(i=2, text="the", start=0.6, end=0.8, probability=0.99),
        Word(i=3, text="show.", start=0.8, end=1.2, probability=0.99),
        Word(i=4, text="Today", start=1.5, end=1.8, probability=0.99),
        Word(i=5, text="we", start=1.8, end=2.0, probability=0.99),
        Word(i=6, text="discuss", start=2.0, end=2.4, probability=0.99),
        Word(i=7, text="AI.", start=2.4, end=2.8, probability=0.99),
        Word(i=8, text="This", start=3.0, end=3.3, probability=0.99),
        Word(i=9, text="is", start=3.3, end=3.5, probability=0.99),
        Word(i=10, text="incredible.", start=3.5, end=4.2, probability=0.99),
    ]
    phrases = [
        Phrase(id="p0", text="Welcome to the show.", start=0.0, end=1.2, speech_start=0.0, speech_end=1.2, word_indices=[0, 1, 2, 3], words=words[0:4]),
        Phrase(id="p1", text="Today we discuss AI.", start=1.5, end=2.8, speech_start=1.5, speech_end=2.8, word_indices=[4, 5, 6, 7], words=words[4:8]),
        Phrase(id="p2", text="This is incredible.", start=3.0, end=4.2, speech_start=3.0, speech_end=4.2, word_indices=[8, 9, 10], words=words[8:11]),
    ]

    planner = RulePlanner()

    # 1. When multi_style_variety=True: styles rotate across sentences
    events_variety = planner.plan(
        phrases=phrases,
        words=words,
        video_duration=5.0,
        multi_style_variety=True,
    )
    styles_variety = [e.style for e in events_variety]
    assert len(set(styles_variety)) >= 2, f"Expected multiple rotating styles, got {styles_variety}"

    # 2. When multi_style_variety=False: locked to single consistent style
    events_locked = planner.plan(
        phrases=phrases,
        words=words,
        video_duration=5.0,
        multi_style_variety=False,
    )
    styles_locked = [e.style for e in events_locked]
    assert len(set(styles_locked)) == 1, f"Expected exactly 1 locked style, got {styles_locked}"


def test_feature_event_long_take_subdivision():
    """Verify that multi-phrase LLM events (>6 words) are safely subdivided into 3-5 word chunks."""
    words = [Word(i=i, text=f"word{i}", start=i*0.5, end=(i+1)*0.5, probability=0.99) for i in range(15)]
    phrases = [
        Phrase(id="p0", text="word0 word1 word2 word3", start=0.0, end=2.0, speech_start=0.0, speech_end=2.0, word_indices=[0, 1, 2, 3], words=words[0:4]),
        Phrase(id="p1", text="word4 word5 word6 word7", start=2.0, end=4.0, speech_start=2.0, speech_end=4.0, word_indices=[4, 5, 6, 7], words=words[4:8]),
        Phrase(id="p2", text="word8 word9 word10 word11", start=4.0, end=6.0, speech_start=4.0, speech_end=6.0, word_indices=[8, 9, 10, 11], words=words[8:12]),
    ]

    # LLM returned an event spanning all 12 words (0 to 11)
    llm_json = [
        {
            "id": "feat_long_1",
            "style": "hormozi_bold",
            "start": 0.0,
            "end": 6.0,
            "wordRange": [0, 11],
            "text": "word0 word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11",
        }
    ]

    subdivided = _validate_and_parse_llm_json(
        raw_text=json.dumps(llm_json),
        phrases=phrases,
        video_duration=7.5,
    )

    # Must be subdivided into 3 phrase-level events matching phrases 0, 1, 2
    assert len(subdivided) == 3, f"Expected 3 subdivided events, got {len(subdivided)}"
    for idx, ev in enumerate(subdivided):
        w_count = ev.wordRange[1] - ev.wordRange[0] + 1
        assert w_count <= 5, f"Subdivided event {ev.id} exceeded 5 words ({w_count} words)"
        assert ev.start >= phrases[idx].start
        assert ev.end <= phrases[idx].end + 0.1


def test_slice_timeline_multi_style_variety_toggle():
    """Verify slice_timeline_for_clip locks to 1 style when multi_style_variety=False."""
    raw_timeline = {
        "version": "1.0",
        "video": {"src": "video.mp4", "durationSec": 60.0, "width": 1080, "height": 1920, "fps": 30},
        "events": [
            {"id": "ev1", "style": "pill_word", "start": 5.0, "end": 8.0, "wordRange": [0, 3], "text": "First clip sentence."},
            {"id": "ev2", "style": "hormozi_bold", "start": 8.2, "end": 11.5, "wordRange": [4, 7], "text": "Second clip sentence."},
            {"id": "ev3", "style": "highlighter_marker", "start": 12.0, "end": 15.0, "wordRange": [8, 11], "text": "Third clip sentence."},
        ],
        "words": [{"i": i, "text": f"w{i}", "start": float(i), "end": float(i) + 0.8} for i in range(20)],
    }
    timeline = Timeline.model_validate(raw_timeline)

    # 1. When multi_style_variety=True: rotates across selected_styles
    sliced_variety = slice_timeline_for_clip(
        timeline=timeline,
        clip_start=4.0,
        clip_end=16.0,
        selected_styles="beast_impact,highlighter_marker,hormozi_bold",
        multi_style_variety=True,
    )
    styles_variety = [e.style for e in sliced_variety.events]
    assert len(set(styles_variety)) >= 2, f"Expected variety across clip, got {styles_variety}"

    # 2. When multi_style_variety=False: locks all clip events to a single style
    sliced_locked = slice_timeline_for_clip(
        timeline=timeline,
        clip_start=4.0,
        clip_end=16.0,
        selected_styles="beast_impact,highlighter_marker,hormozi_bold",
        multi_style_variety=False,
    )
    styles_locked = [e.style for e in sliced_locked.events]
    assert len(set(styles_locked)) == 1, f"Expected single locked style, got {styles_locked}"
    assert styles_locked[0] == "beast_impact"
