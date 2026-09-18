"""YouTube video lookup/download via yt-dlp.

NOTICE: Downloading YouTube videos with yt-dlp can conflict with YouTube's
Terms of Service. This project downloads videos solely for personal,
non-commercial technique analysis (see README). Do not redistribute
downloaded files, and get legal review before turning this into a public
service.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yt_dlp

_YOUTUBE_ID_RE = re.compile(
    r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|shorts/|embed/|live/))([A-Za-z0-9_-]{11})"
)


class VideoDownloadError(Exception):
    """Base class for user-facing download failures."""


class InvalidUrlError(VideoDownloadError):
    pass


class PrivateVideoError(VideoDownloadError):
    pass


class AgeRestrictedVideoError(VideoDownloadError):
    pass


class VideoUnavailableError(VideoDownloadError):
    pass


class DurationExceededError(VideoDownloadError):
    def __init__(self, duration_sec: int, max_duration_sec: int) -> None:
        self.duration_sec = duration_sec
        self.max_duration_sec = max_duration_sec
        super().__init__(
            f"Video is {duration_sec // 60}min, which exceeds the "
            f"{max_duration_sec // 60}min processing limit."
        )


@dataclass
class DownloadResult:
    video_id: str
    title: str
    thumbnail_url: str | None
    duration_sec: int
    local_path: str


def extract_video_id(url: str) -> str:
    """Parse a YouTube video id out of a URL without hitting the network.

    Used at registration time to dedupe against already-downloaded videos
    before paying the cost of a real yt-dlp download.
    """
    match = _YOUTUBE_ID_RE.search(url)
    if match:
        return match.group(1)
    raise InvalidUrlError(f"Could not parse a YouTube video id from url: {url}")


def _map_download_error(url: str, exc: Exception) -> VideoDownloadError:
    message = str(exc).lower()
    if "private video" in message:
        return PrivateVideoError(f"This video is private and cannot be downloaded: {url}")
    if "age" in message and "restrict" in message:
        return AgeRestrictedVideoError(f"This video is age-restricted and cannot be downloaded: {url}")
    if any(term in message for term in ("video unavailable", "has been removed", "does not exist")):
        return VideoUnavailableError(f"This video is unavailable or has been deleted: {url}")
    return VideoUnavailableError(f"Failed to download video ({exc})")


def download_video(url: str, download_dir: Path, max_duration_sec: int) -> DownloadResult:
    """Download `url` with yt-dlp, raising a specific VideoDownloadError on failure.

    Duration is checked from metadata before the actual download starts so we
    don't pay bandwidth for videos we're going to reject anyway.
    """
    download_dir.mkdir(parents=True, exist_ok=True)
    ydl_opts = {
        "format": "mp4/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
        "outtmpl": str(download_dir / "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        # The "web" client increasingly demands a sign-in/PO token from
        # datacenter IPs (which is what a Render-hosted server looks like to
        # YouTube). "android"/"ios" clients don't require that handshake, so
        # try those first and only fall back to "web" for videos they can't
        # resolve.
        "extractor_args": {"youtube": {"player_client": ["android", "ios", "web"]}},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            duration_sec = int(info.get("duration") or 0)
            if duration_sec and duration_sec > max_duration_sec:
                raise DurationExceededError(duration_sec, max_duration_sec)

            info = ydl.extract_info(url, download=True)
            local_path = ydl.prepare_filename(info)
    except DurationExceededError:
        raise
    except yt_dlp.utils.DownloadError as exc:
        raise _map_download_error(url, exc) from exc

    return DownloadResult(
        video_id=info["id"],
        title=info.get("title") or info["id"],
        thumbnail_url=info.get("thumbnail"),
        duration_sec=duration_sec or int(info.get("duration") or 0),
        local_path=local_path,
    )
