from __future__ import annotations

from unittest.mock import patch

from app.models.video import AnalysisSegment, Video, VideoStatus
from app.services.llm_analysis import LLMConfigurationError, MatchResult


class FakeAnalyzer:
    def rank_segments(self, query, segments):
        return [MatchResult(segment_index=0, confidence=0.87, description="First stroke after push-off")]

    def analyze_video(self, local_path):  # pragma: no cover - unused here
        raise NotImplementedError


def _seed_completed_video(db_session) -> None:
    video = Video(
        youtube_url="https://youtu.be/abc123",
        video_id="abc123",
        title="Olympic Freestyle Technique",
        status=VideoStatus.COMPLETED,
    )
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)
    db_session.add(AnalysisSegment(video_pk=video.id, start_sec=125, end_sec=131, description="stroke"))
    db_session.commit()


def test_search_returns_expected_shape(client, db_session):
    _seed_completed_video(db_session)

    with patch("app.api.search.get_llm_analyzer", return_value=FakeAnalyzer()):
        response = client.post("/api/search", json={"query": "자유형 턴에서 팔을 젓는 모습"})

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "자유형 턴에서 팔을 젓는 모습"
    assert len(body["results"]) == 1
    result = body["results"][0]
    assert result["video_id"] == "abc123"
    assert result["video_title"] == "Olympic Freestyle Technique"
    assert result["start_sec"] == 125
    assert result["end_sec"] == 131
    assert result["confidence"] == 0.87
    assert result["description"]


def test_search_returns_503_when_llm_not_configured(client, db_session):
    _seed_completed_video(db_session)

    with patch("app.api.search.get_llm_analyzer", side_effect=LLMConfigurationError("no key")):
        response = client.post("/api/search", json={"query": "turn"})

    assert response.status_code == 503
