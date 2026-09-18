from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import yt_dlp

from app.services import youtube


def test_extract_video_id_watch_url():
    assert youtube.extract_video_id("https://www.youtube.com/watch?v=abc12345678") == "abc12345678"


def test_extract_video_id_short_url():
    assert youtube.extract_video_id("https://youtu.be/abc12345678") == "abc12345678"


def test_extract_video_id_invalid_url():
    with pytest.raises(youtube.InvalidUrlError):
        youtube.extract_video_id("https://example.com/not-a-video")


@patch("app.services.youtube.yt_dlp.YoutubeDL")
def test_fetch_video_metadata_success(mock_ydl_cls):
    mock_ydl = MagicMock()
    mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.return_value = {
        "id": "abc12345678",
        "title": "Test Swim",
        "thumbnail": "http://x/thumb.jpg",
        "duration": 60,
    }

    result = youtube.fetch_video_metadata("https://youtu.be/abc12345678", max_duration_sec=3600)

    assert result.video_id == "abc12345678"
    assert result.title == "Test Swim"
    assert result.duration_sec == 60
    mock_ydl.extract_info.assert_called_once_with("https://youtu.be/abc12345678", download=False)


@patch("app.services.youtube.yt_dlp.YoutubeDL")
def test_fetch_video_metadata_duration_exceeded(mock_ydl_cls):
    mock_ydl = MagicMock()
    mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.return_value = {"id": "abc", "duration": 7200}

    with pytest.raises(youtube.DurationExceededError):
        youtube.fetch_video_metadata("https://youtu.be/abc12345678", max_duration_sec=3600)


@patch("app.services.youtube.yt_dlp.YoutubeDL")
def test_fetch_video_metadata_private(mock_ydl_cls):
    mock_ydl = MagicMock()
    mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.side_effect = yt_dlp.utils.DownloadError("ERROR: Private video")

    with pytest.raises(youtube.PrivateVideoError):
        youtube.fetch_video_metadata("https://youtu.be/abc12345678", max_duration_sec=3600)


@patch("app.services.youtube.yt_dlp.YoutubeDL")
def test_fetch_video_metadata_unavailable(mock_ydl_cls):
    mock_ydl = MagicMock()
    mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.side_effect = yt_dlp.utils.DownloadError("Video unavailable")

    with pytest.raises(youtube.VideoUnavailableError):
        youtube.fetch_video_metadata("https://youtu.be/abc12345678", max_duration_sec=3600)
