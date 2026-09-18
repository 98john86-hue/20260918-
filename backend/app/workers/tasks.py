"""Background task entry points.

Today these run in-process via FastAPI's BackgroundTasks. Each function only
opens its own DB session and delegates to app/services — to move to Celery,
wrap `run_video_processing` as `@celery_app.task` and call `.delay(video_pk)`
instead of `background_tasks.add_task(...)`; no service code changes.
"""
from __future__ import annotations

import logging

from app.database import SessionLocal
from app.services.video_processor import process_video

logger = logging.getLogger(__name__)


def run_video_processing(video_pk: int) -> None:
    db = SessionLocal()
    try:
        process_video(db, video_pk)
    except Exception:  # noqa: BLE001 - last-resort guard so a bug doesn't leave status stuck
        logger.exception("Unhandled error while processing video_pk=%s", video_pk)
    finally:
        db.close()
