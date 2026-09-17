from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.video import VideoStatus


class VideoCreateRequest(BaseModel):
    youtube_url: str = Field(..., description="A youtube.com or youtu.be video URL")


class VideoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    youtube_url: str
    video_id: str
    title: str | None
    thumbnail_url: str | None
    duration_sec: int | None
    status: VideoStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class VideoListResponse(BaseModel):
    videos: list[VideoResponse]
