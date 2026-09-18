from __future__ import annotations

from app.models.video import AnalysisSegment, Video, VideoStatus
from app.services.llm_analysis import MatchResult, SceneSegment
from app.services.search import search_library


class FakeAnalyzer:
    def __init__(self, matches_by_call):
        self._matches_by_call = matches_by_call
        self.calls = 0

    def rank_segments(self, query: str, segments: list[SceneSegment]) -> list[MatchResult]:
        matches = self._matches_by_call[self.calls]
        self.calls += 1
        return matches

    def analyze_video(self, youtube_url: str):  # pragma: no cover - unused here
        raise NotImplementedError


def _make_video(db, video_id: str, title: str, status=VideoStatus.COMPLETED) -> Video:
    video = Video(youtube_url=f"https://youtu.be/{video_id}", video_id=video_id, title=title, status=status)
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


def test_search_library_aggregates_and_sorts_across_videos(db_session):
    v1 = _make_video(db_session, "vid1", "Video One")
    db_session.add(AnalysisSegment(video_pk=v1.id, start_sec=10, end_sec=15, description="turn A"))
    v2 = _make_video(db_session, "vid2", "Video Two")
    db_session.add(AnalysisSegment(video_pk=v2.id, start_sec=20, end_sec=25, description="turn B"))
    db_session.commit()

    analyzer = FakeAnalyzer(
        [
            [MatchResult(segment_index=0, confidence=0.4, description="low match")],
            [MatchResult(segment_index=0, confidence=0.9, description="high match")],
        ]
    )

    results = search_library(db_session, analyzer, "freestyle turn", top_k=5)

    assert [r.video_id for r in results] == ["vid2", "vid1"]
    assert results[0].confidence == 0.9


def test_search_library_skips_videos_without_segments(db_session):
    _make_video(db_session, "vid1", "No segments yet")
    analyzer = FakeAnalyzer([])

    results = search_library(db_session, analyzer, "freestyle turn", top_k=5)

    assert results == []
    assert analyzer.calls == 0


def test_search_library_ignores_non_completed_videos(db_session):
    v1 = _make_video(db_session, "vid1", "Still analyzing", status=VideoStatus.ANALYZING)
    db_session.add(AnalysisSegment(video_pk=v1.id, start_sec=1, end_sec=2, description="x"))
    db_session.commit()
    analyzer = FakeAnalyzer([])

    results = search_library(db_session, analyzer, "freestyle turn", top_k=5)

    assert results == []


def test_search_library_respects_top_k(db_session):
    v1 = _make_video(db_session, "vid1", "V1")
    db_session.add(AnalysisSegment(video_pk=v1.id, start_sec=1, end_sec=2, description="a"))
    db_session.add(AnalysisSegment(video_pk=v1.id, start_sec=3, end_sec=4, description="b"))
    db_session.commit()

    analyzer = FakeAnalyzer(
        [
            [
                MatchResult(segment_index=0, confidence=0.7, description="a-match"),
                MatchResult(segment_index=1, confidence=0.6, description="b-match"),
            ]
        ]
    )

    results = search_library(db_session, analyzer, "query", top_k=1)

    assert len(results) == 1
    assert results[0].confidence == 0.7
