from __future__ import annotations

from pathlib import Path
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
def test_download_video_success(mock_ydl_cls, tmp_path: Path):
    mock_ydl = MagicMock()
    mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
    info = {"id": "abc12345678", "title": "Test Swim", "thumbnail": "http://x/thumb.jpg", "duration": 60}
    mock_ydl.extract_info.side_effect = [info, info]
    mock_ydl.prepare_filename.return_value = str(tmp_path / "abc12345678.mp4")

    result = youtube.download_video("https://youtu.be/abc12345678", tmp_path, max_duration_sec=3600)

    assert result.video_id == "abc12345678"
    assert result.title == "Test Swim"
    assert result.duration_sec == 60


@patch("app.services.youtube.yt_dlp.YoutubeDL")
def test_download_video_duration_exceeded(mock_ydl_cls, tmp_path: Path):
    mock_ydl = MagicMock()
    mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.return_value = {"id": "abc", "duration": 7200}

    with pytest.raises(youtube.DurationExceededError):
        youtube.download_video("https://youtu.be/abc12345678", tmp_path, max_duration_sec=3600)


@patch("app.services.youtube.yt_dlp.YoutubeDL")
def test_download_video_private(mock_ydl_cls, tmp_path: Path):
    mock_ydl = MagicMock()
    mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.side_effect = yt_dlp.utils.DownloadError("ERROR: Private video")

    with pytest.raises(youtube.PrivateVideoError):
        youtube.download_video("https://youtu.be/abc12345678", tmp_path, max_duration_sec=3600)


@patch("app.services.youtube.yt_dlp.YoutubeDL")
def test_download_video_unavailable(mock_ydl_cls, tmp_path: Path):
    mock_ydl = MagicMock()
    mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.side_effect = yt_dlp.utils.DownloadError("Video unavailable")

    with pytest.raises(youtube.VideoUnavailableError):
        youtube.download_video("https://youtu.be/abc12345678", tmp_path, max_duration_sec=3600)
