from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.config import Settings
from app.services.llm_analysis import (
    GeminiAnalyzer,
    LLMConfigurationError,
    MatchResult,
    SceneSegment,
    TransientLLMError,
    get_llm_analyzer,
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


@patch("google.genai.Client")
def test_gemini_analyzer_retries_then_succeeds(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    ok_response = MagicMock(text='[{"segment_index": 0, "confidence": 0.5, "description": "ok"}]')
    mock_client.models.generate_content.side_effect = [RuntimeError("timeout"), ok_response]

    analyzer = GeminiAnalyzer(
        api_key="fake-key", model_name="gemini-3.5-flash-lite", max_retries=4, min_wait=0.01, max_wait=0.02
    )
    result = analyzer.rank_segments("turn", [SceneSegment(0, 1, "desc")])

    assert result[0].confidence == 0.5
    assert mock_client.models.generate_content.call_count == 2


@patch("google.genai.Client")
def test_gemini_analyzer_gives_up_after_max_retries(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.models.generate_content.side_effect = RuntimeError("always fails")

    analyzer = GeminiAnalyzer(
        api_key="fake-key", model_name="gemini-3.5-flash-lite", max_retries=3, min_wait=0.01, max_wait=0.02
    )

    with pytest.raises(TransientLLMError):
        analyzer.rank_segments("turn", [SceneSegment(0, 1, "desc")])
    assert mock_client.models.generate_content.call_count == 3


@patch("google.genai.Client")
def test_gemini_analyzer_analyze_video_sends_youtube_url_as_file_uri(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.models.generate_content.return_value = MagicMock(
        text='[{"start_sec": 1.0, "end_sec": 2.0, "description": "Turn"}]'
    )

    analyzer = GeminiAnalyzer(
        api_key="fake-key", model_name="gemini-3.5-flash-lite", max_retries=1, min_wait=0.01, max_wait=0.02
    )
    result = analyzer.analyze_video("https://www.youtube.com/watch?v=abc12345678")

    assert result == [SceneSegment(start_sec=1.0, end_sec=2.0, description="Turn")]
    contents = mock_client.models.generate_content.call_args.kwargs["contents"]
    assert contents[0].file_data.file_uri == "https://www.youtube.com/watch?v=abc12345678"


@patch("app.services.llm_analysis.get_settings")
def test_get_llm_analyzer_raises_when_no_key_anywhere(mock_get_settings):
    mock_get_settings.return_value = Settings(gemini_api_key=None)

    with pytest.raises(LLMConfigurationError):
        get_llm_analyzer()


@patch("google.genai.Client")
@patch("app.services.llm_analysis.get_settings")
def test_get_llm_analyzer_uses_caller_supplied_key_when_server_has_none(mock_get_settings, mock_client_cls):
    mock_get_settings.return_value = Settings(gemini_api_key=None)

    get_llm_analyzer(api_key="user-supplied-key")

    mock_client_cls.assert_called_once_with(api_key="user-supplied-key")


@patch("google.genai.Client")
@patch("app.services.llm_analysis.get_settings")
def test_get_llm_analyzer_prefers_caller_supplied_key_over_server_key(mock_get_settings, mock_client_cls):
    mock_get_settings.return_value = Settings(gemini_api_key="server-key")

    get_llm_analyzer(api_key="user-supplied-key")

    mock_client_cls.assert_called_once_with(api_key="user-supplied-key")
