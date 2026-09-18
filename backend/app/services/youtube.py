"""YouTube video lookup: title/thumbnail via oEmbed, duration via yt-dlp.

The video itself is never downloaded: Gemini can analyze a public YouTube
video directly from its URL (see services/llm_analysis.py). Metadata is
split across two sources because YouTube's bot/sign-in wall for datacenter
IPs (which is what a Render-hosted server looks like) increasingly blocks
yt-dlp's extraction pipeline even for metadata-only lookups:

- title/thumbnail come from YouTube's public oEmbed endpoint, a plain
  unauthenticated JSON API that isn't part of that extraction pipeline and
  so isn't subject to the bot wall.
- duration still goes through yt-dlp, but only as a best-effort pre-flight
  check (see _probe_duration_sec): if it's blocked, registration proceeds
  without enforcing the duration limit for that video rather than failing
  outright, since title/thumbnail (and the actual analysis, via Gemini) do
  not depend on it.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import httpx
import yt_dlp

logger = logging.getLogger(__name__)

_YOUTUBE_ID_RE = re.compile(
    r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|shorts/|embed/|live/))([A-Za-z0-9_-]{11})"
)
_OEMBED_URL = "https://www.youtube.com/oembed"


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


def _fetch_oembed(url: str) -> dict:
    try:
        response = httpx.get(_OEMBED_URL, params={"url": url, "format": "json"}, timeout=10.0)
    except httpx.HTTPError as exc:
        raise VideoUnavailableError(f"Failed to look up video ({exc})") from exc

    if response.status_code in (401, 403):
        raise PrivateVideoError(f"This video is private and cannot be analyzed: {url}")
    if response.status_code == 404:
        raise VideoUnavailableError(f"This video is unavailable or has been deleted: {url}")
    if response.status_code != 200:
        raise VideoUnavailableError(f"Failed to look up video (HTTP {response.status_code}): {url}")

    return response.json()


def _probe_duration_sec(url: str) -> int | None:
    """Best-effort duration lookup via yt-dlp; None if the extractor is blocked.

    See module docstring: unlike oEmbed, this hits the same yt-dlp
    extraction pipeline YouTube's bot wall targets, so failures here are
    expected and must not block registration.
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        # The "web" client increasingly demands a sign-in/PO token from
        # datacenter IPs. "android"/"ios" clients don't require that
        # handshake, so try those first and only fall back to "web".
        "extractor_args": {"youtube": {"player_client": ["android", "ios", "web"]}},
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return int(info.get("duration") or 0) or None
    except Exception as exc:  # noqa: BLE001 - duration probing is best-effort only
        logger.info("Duration probe failed for %s, skipping pre-flight duration check: %s", url, exc)
        return None


def fetch_video_metadata(url: str, max_duration_sec: int) -> VideoMetadata:
    """Resolve `url`'s title/thumbnail/duration, raising a VideoDownloadError on failure."""
    video_id = extract_video_id(url)
    oembed = _fetch_oembed(url)

    duration_sec = _probe_duration_sec(url)
    if duration_sec and duration_sec > max_duration_sec:
        raise DurationExceededError(duration_sec, max_duration_sec)

    return VideoMetadata(
        video_id=video_id,
        title=oembed.get("title") or video_id,
        thumbnail_url=oembed.get("thumbnail_url"),
        duration_sec=duration_sec or 0,
    )
