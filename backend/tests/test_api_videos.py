from __future__ import annotations

from unittest.mock import patch


def test_register_video_creates_pending_video(client):
    with patch("app.api.videos.run_video_processing") as mock_task:
        response = client.post("/api/videos", json={"youtube_url": "https://youtu.be/abc12345678"})

    assert response.status_code == 201
    body = response.json()
    assert body["video_id"] == "abc12345678"
    assert body["status"] == "pending"
    mock_task.assert_called_once()


def test_register_video_dedupes_same_video_id(client):
    with patch("app.api.videos.run_video_processing") as mock_task:
        first = client.post("/api/videos", json={"youtube_url": "https://youtu.be/abc12345678"})
        second = client.post("/api/videos", json={"youtube_url": "https://www.youtube.com/watch?v=abc12345678"})

    assert first.json()["id"] == second.json()["id"]
    mock_task.assert_called_once()


def test_register_video_invalid_url_returns_422(client):
    response = client.post("/api/videos", json={"youtube_url": "https://example.com/not-a-video"})
    assert response.status_code == 422


def test_list_videos(client):
    with patch("app.api.videos.run_video_processing"):
        client.post("/api/videos", json={"youtube_url": "https://youtu.be/abc12345678"})

    response = client.get("/api/videos")
    assert response.status_code == 200
    assert len(response.json()["videos"]) == 1


def test_get_video_not_found(client):
    response = client.get("/api/videos/999")
    assert response.status_code == 404
