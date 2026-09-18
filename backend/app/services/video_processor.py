"""Registration + processing orchestration for a single video.

Split out from app/api/videos.py and app/workers/tasks.py so the same logic
can run from a FastAPI BackgroundTasks callback today and from a Celery task
later with no changes beyond the wrapper (see workers/tasks.py).
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.video import AnalysisSegment, Video, VideoStatus
from app.services import youtube
from app.services.llm_analysis import LLMConfigurationError, get_llm_analyzer

logger = logging.getLogger(__name__)


def process_video(db: Session, video_pk: int) -> None:
    video = db.get(Video, video_pk)
    if video is None:
        logger.error("process_video called for missing video pk=%s", video_pk)
        return

    settings = get_settings()

    video.status = VideoStatus.DOWNLOADING
    video.error_message = None
    db.commit()

    try:
        metadata = youtube.fetch_video_metadata(video.youtube_url, settings.max_video_duration_sec)
    except youtube.VideoDownloadError as exc:
        video.status = VideoStatus.FAILED
        video.error_message = str(exc)
        db.commit()
        return

    video.title = metadata.title
    video.thumbnail_url = metadata.thumbnail_url
    video.duration_sec = metadata.duration_sec
    video.status = VideoStatus.ANALYZING
    db.commit()

    try:
        analyzer = get_llm_analyzer()
        segments = analyzer.analyze_video(video.youtube_url)
    except LLMConfigurationError as exc:
        video.status = VideoStatus.FAILED
        video.error_message = str(exc)
        db.commit()
        return
    except Exception as exc:  # noqa: BLE001 - surface any analysis failure to the user
        logger.exception("Video analysis failed for video_pk=%s", video_pk)
        video.status = VideoStatus.FAILED
        video.error_message = f"Analysis failed: {exc}"
        db.commit()
        return

    for segment in segments:
        db.add(
            AnalysisSegment(
                video_pk=video.id,
                start_sec=segment.start_sec,
                end_sec=segment.end_sec,
                description=segment.description,
            )
        )
    video.status = VideoStatus.COMPLETED
    db.commit()
