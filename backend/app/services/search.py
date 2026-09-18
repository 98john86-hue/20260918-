"""Search matching: rank cached analysis segments against a user query.

Kept as a thin function over `LLMAnalyzer.rank_segments` (rather than baked
into the API layer) so Phase 2 can swap this implementation for a pgvector
similarity query without touching app/api/search.py.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.video import Video, VideoStatus
from app.schemas.search import SearchResultItem
from app.services.llm_analysis import LLMAnalyzer, MatchResult, SceneSegment


def search_library(db: Session, analyzer: LLMAnalyzer, query: str, top_k: int) -> list[SearchResultItem]:
    videos = (
        db.query(Video)
        .filter(Video.status == VideoStatus.COMPLETED)
        .all()
    )

    all_results: list[SearchResultItem] = []
    for video in videos:
        if not video.segments:
            continue
        scene_segments = [
            SceneSegment(start_sec=s.start_sec, end_sec=s.end_sec, description=s.description)
            for s in video.segments
        ]
        matches: list[MatchResult] = analyzer.rank_segments(query, scene_segments)
        for match in matches:
            if not (0 <= match.segment_index < len(scene_segments)):
                continue
            segment = scene_segments[match.segment_index]
            all_results.append(
                SearchResultItem(
                    video_id=video.video_id,
                    video_title=video.title,
                    thumbnail_url=video.thumbnail_url,
                    start_sec=segment.start_sec,
                    end_sec=segment.end_sec,
                    confidence=match.confidence,
                    description=match.description or segment.description,
                )
            )

    all_results.sort(key=lambda r: r.confidence, reverse=True)
    return all_results[:top_k]
