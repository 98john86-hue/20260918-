"""YouTube video lookup via yt-dlp.

The video itself is never downloaded: Gemini can analyze a public YouTube
video directly from its URL (see services/llm_analysis.py), so this module
only resolves lightweight metadata (title, thumbnail, duration) up front, to
populate the library UI and enforce the duration limit before an expensive
LLM call.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import yt_dlp

_YOUTUBE_ID_RE = re.compile(
    r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|shorts/|embed/|live/))([A-Za-z0-9_-]{11})"
)


class VideoDownloadError(Exception):
    """Base class for user-facing video lookup failures."""


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
class VideoMetadata:
    video_id: str
    title: str
    thumbnail_url: str | None
    duration_sec: int


def extract_video_id(url: str) -> str:
    """Parse a YouTube video id out of a URL without hitting the network.

    Used at registration time to dedupe against already-registered videos
    before paying the cost of a metadata lookup.
    """
    match = _YOUTUBE_ID_RE.search(url)
    if match:
        return match.group(1)
    raise InvalidUrlError(f"Could not parse a YouTube video id from url: {url}")


def _map_lookup_error(url: str, exc: Exception) -> VideoDownloadError:
    message = str(exc).lower()
    if "private video" in message:
        return PrivateVideoError(f"This video is private and cannot be analyzed: {url}")
    if "age" in message and "restrict" in message:
        return AgeRestrictedVideoError(f"This video is age-restricted and cannot be analyzed: {url}")
    if any(term in message for term in ("video unavailable", "has been removed", "does not exist")):
        return VideoUnavailableError(f"This video is unavailable or has been deleted: {url}")
    return VideoUnavailableError(f"Failed to look up video ({exc})")


def fetch_video_metadata(url: str, max_duration_sec: int) -> VideoMetadata:
    """Resolve `url`'s title/thumbnail/duration, raising a VideoDownloadError on failure.

    This is a metadata-only yt-dlp call (no video bytes are fetched).
    """
    ydl_opts = {
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
    except DurationExceededError:
        raise
    except yt_dlp.utils.DownloadError as exc:
        raise _map_lookup_error(url, exc) from exc

    return VideoMetadata(
        video_id=info["id"],
        title=info.get("title") or info["id"],
        thumbnail_url=info.get("thumbnail"),
        duration_sec=duration_sec,
    )
