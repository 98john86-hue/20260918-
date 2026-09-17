from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.llm_analysis import (
    GeminiAnalyzer,
    MatchResult,
    SceneSegment,
    TransientLLMError,
    parse_match_results,
    parse_scene_segments,
)


def test_parse_scene_segments_plain_json():
    raw = '[{"start_sec": 12.0, "end_sec": 18.5, "description": "Flip turn"}]'
    segments = parse_scene_segments(raw)
    assert segments == [SceneSegment(start_sec=12.0, end_sec=18.5, description="Flip turn")]


def test_parse_scene_segments_strips_code_fence():
    raw = '```json\n[{"start_sec": 1, "end_sec": 2, "description": "Start"}]\n```'
    segments = parse_scene_segments(raw)
    assert segments[0].description == "Start"


def test_parse_match_results():
    raw = '[{"segment_index": 0, "confidence": 0.9, "description": "Great match"}]'
    matches = parse_match_results(raw)
    assert matches == [MatchResult(segment_index=0, confidence=0.9, description="Great match")]


@patch("google.generativeai.configure")
@patch("google.generativeai.GenerativeModel")
def test_gemini_analyzer_retries_then_succeeds(mock_model_cls, _mock_configure):
    mock_model = MagicMock()
    mock_model_cls.return_value = mock_model

    ok_response = MagicMock(text='[{"segment_index": 0, "confidence": 0.5, "description": "ok"}]')
    mock_model.generate_content.side_effect = [RuntimeError("timeout"), ok_response]

    analyzer = GeminiAnalyzer(
        api_key="fake-key", model_name="gemini-1.5-flash", max_retries=4, min_wait=0.01, max_wait=0.02
    )
    result = analyzer.rank_segments("turn", [SceneSegment(0, 1, "desc")])

    assert result[0].confidence == 0.5
    assert mock_model.generate_content.call_count == 2


@patch("google.generativeai.configure")
@patch("google.generativeai.GenerativeModel")
def test_gemini_analyzer_gives_up_after_max_retries(mock_model_cls, _mock_configure):
    mock_model = MagicMock()
    mock_model_cls.return_value = mock_model
    mock_model.generate_content.side_effect = RuntimeError("always fails")

    analyzer = GeminiAnalyzer(
        api_key="fake-key", model_name="gemini-1.5-flash", max_retries=3, min_wait=0.01, max_wait=0.02
    )

    with pytest.raises(TransientLLMError):
        analyzer.rank_segments("turn", [SceneSegment(0, 1, "desc")])
    assert mock_model.generate_content.call_count == 3
