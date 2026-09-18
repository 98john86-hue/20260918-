from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.video import Video, VideoStatus
from app.schemas.video import VideoCreateRequest, VideoListResponse, VideoResponse
from app.services import youtube
from app.workers.tasks import run_video_processing

router = APIRouter(prefix="/api/videos", tags=["videos"])


@router.post("", response_model=VideoResponse, status_code=201)
def register_video(
    payload: VideoCreateRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
) -> Video:
    try:
        video_id = youtube.extract_video_id(payload.youtube_url)
    except youtube.InvalidUrlError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    existing = db.query(Video).filter(Video.video_id == video_id).one_or_none()
    if existing is not None:
        # Same YouTube video already registered: never re-download/re-analyze
        # a COMPLETED video, and don't kick off a duplicate in-flight job.
        if existing.status == VideoStatus.FAILED:
            existing.status = VideoStatus.PENDING
            existing.error_message = None
            db.commit()
            db.refresh(existing)
            background_tasks.add_task(run_video_processing, existing.id)
        return existing

    video = Video(youtube_url=payload.youtube_url, video_id=video_id, status=VideoStatus.PENDING)
    db.add(video)
    db.commit()
    db.refresh(video)

    background_tasks.add_task(run_video_processing, video.id)
    return video


@router.get("", response_model=VideoListResponse)
def list_videos(db: Session = Depends(get_db)) -> VideoListResponse:
    videos = db.query(Video).order_by(Video.created_at.desc()).all()
    return VideoListResponse(videos=videos)


@router.get("/{video_pk}", response_model=VideoResponse)
def get_video(video_pk: int, db: Session = Depends(get_db)) -> Video:
    video = db.get(Video, video_pk)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return video
