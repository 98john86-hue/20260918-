from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services import youtube


def test_extract_video_id_watch_url():
    assert youtube.extract_video_id("https://www.youtube.com/watch?v=abc12345678") == "abc12345678"


def test_extract_video_id_short_url():
    assert youtube.extract_video_id("https://youtu.be/abc12345678") == "abc12345678"


def test_extract_video_id_invalid_url():
    with pytest.raises(youtube.InvalidUrlError):
        youtube.extract_video_id("https://example.com/not-a-video")


def _mock_oembed_response(status_code: int, body: dict | None = None) -> MagicMock:
    return MagicMock(status_code=status_code, json=MagicMock(return_value=body or {}))


@patch("app.services.youtube.yt_dlp.YoutubeDL")
@patch("app.services.youtube.httpx.get")
def test_fetch_video_metadata_success(mock_get, mock_ydl_cls):
    mock_get.return_value = _mock_oembed_response(
        200, {"title": "Test Swim", "thumbnail_url": "http://x/thumb.jpg"}
    )
    mock_ydl = MagicMock()
    mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.return_value = {"duration": 60}

    result = youtube.fetch_video_metadata("https://youtu.be/abc12345678", max_duration_sec=3600)

    assert result.video_id == "abc12345678"
    assert result.title == "Test Swim"
    assert result.thumbnail_url == "http://x/thumb.jpg"
    assert result.duration_sec == 60


@patch("app.services.youtube.yt_dlp.YoutubeDL")
@patch("app.services.youtube.httpx.get")
def test_fetch_video_metadata_duration_exceeded(mock_get, mock_ydl_cls):
    mock_get.return_value = _mock_oembed_response(200, {"title": "Long video"})
    mock_ydl = MagicMock()
    mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.return_value = {"duration": 7200}

    with pytest.raises(youtube.DurationExceededError):
        youtube.fetch_video_metadata("https://youtu.be/abc12345678", max_duration_sec=3600)


@patch("app.services.youtube.yt_dlp.YoutubeDL")
@patch("app.services.youtube.httpx.get")
def test_fetch_video_metadata_survives_blocked_duration_probe(mock_get, mock_ydl_cls):
    """yt-dlp is blocked (bot wall) but oEmbed still resolves the video: registration proceeds."""
    mock_get.return_value = _mock_oembed_response(
        200, {"title": "Test Swim", "thumbnail_url": "http://x/thumb.jpg"}
    )
    mock_ydl = MagicMock()
    mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.side_effect = RuntimeError("Sign in to confirm you're not a bot")

    result = youtube.fetch_video_metadata("https://youtu.be/abc12345678", max_duration_sec=3600)

    assert result.title == "Test Swim"
    assert result.duration_sec == 0


@patch("app.services.youtube.httpx.get")
def test_fetch_video_metadata_private(mock_get):
    mock_get.return_value = _mock_oembed_response(401)

    with pytest.raises(youtube.PrivateVideoError):
        youtube.fetch_video_metadata("https://youtu.be/abc12345678", max_duration_sec=3600)


@patch("app.services.youtube.httpx.get")
def test_fetch_video_metadata_unavailable(mock_get):
    mock_get.return_value = _mock_oembed_response(404)

    with pytest.raises(youtube.VideoUnavailableError):
        youtube.fetch_video_metadata("https://youtu.be/abc12345678", max_duration_sec=3600)
