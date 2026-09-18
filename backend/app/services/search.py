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


def _match_video_segments(analyzer: LLMAnalyzer, video: Video, query: str) -> list[SearchResultItem]:
    if not video.segments:
        return []
    scene_segments = [
        SceneSegment(start_sec=s.start_sec, end_sec=s.end_sec, description=s.description)
        for s in video.segments
    ]
    matches: list[MatchResult] = analyzer.rank_segments(query, scene_segments)
    results: list[SearchResultItem] = []
    for match in matches:
        if not (0 <= match.segment_index < len(scene_segments)):
            continue
        segment = scene_segments[match.segment_index]
        results.append(
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
    return results


def search_library(db: Session, analyzer: LLMAnalyzer, query: str, top_k: int) -> list[SearchResultItem]:
    videos = (
        db.query(Video)
        .filter(Video.status == VideoStatus.COMPLETED)
        .all()
    )

    all_results: list[SearchResultItem] = []
    for video in videos:
        all_results.extend(_match_video_segments(analyzer, video, query))

    all_results.sort(key=lambda r: r.confidence, reverse=True)
    return all_results[:top_k]


def search_in_video(analyzer: LLMAnalyzer, video: Video, query: str, top_k: int) -> list[SearchResultItem]:
    """Search for a described motion within a single already-completed video.

    Unlike search_library, the caller is expected to have already resolved
    and validated `video` (exists, status == COMPLETED) so this stays a pure
    ranking step; an empty return means the video has no matching scene, not
    that the video itself couldn't be found.
    """
    results = _match_video_segments(analyzer, video, query)
    results.sort(key=lambda r: r.confidence, reverse=True)
    return results[:top_k]
