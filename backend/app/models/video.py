from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VideoStatus(str, enum.Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class Video(Base):
    """A registered YouTube video and its processing state.

    `video_id` is the YouTube video id (e.g. "abc123"), not the primary key.
    It carries a unique constraint so that re-registering the same YouTube
    video is a no-op (see services/video_processor.py) instead of triggering
    a redundant download + LLM analysis pass.
    """

    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    youtube_url: Mapped[str] = mapped_column(String(512), nullable=False)
    video_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[VideoStatus] = mapped_column(
        Enum(VideoStatus, native_enum=False, length=32), default=VideoStatus.PENDING, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    local_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    segments: Mapped[list["AnalysisSegment"]] = relationship(
        back_populates="video", cascade="all, delete-orphan"
    )


class AnalysisSegment(Base):
    """A cached scene the multimodal LLM identified in a video.

    Produced once per video during the ANALYZING phase and reused for every
    subsequent search query (see services/search.py) so that a video is never
    re-uploaded to the LLM just because a new query came in. Phase 2 adds a
    frame-embedding column/table alongside this for vector similarity search;
    `description` stays as the human-readable fallback either way.
    """

    __tablename__ = "analysis_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_pk: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    start_sec: Mapped[float] = mapped_column(Float, nullable=False)
    end_sec: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Phase 2 placeholders: stroke ("freestyle"/"backstroke"/...) and phase
    # ("start"/"turn"/"stroke"/...) tagging/filtering.
    stroke_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    phase: Mapped[str | None] = mapped_column(String(32), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    video: Mapped["Video"] = relationship(back_populates="segments")
