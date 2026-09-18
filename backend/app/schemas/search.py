from __future__ import annotations

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural-language description of the scene to find")
    top_k: int = Field(default=5, ge=1, le=50)
    gemini_api_key: str | None = Field(
        default=None, description="Caller-supplied Gemini API key; overrides the server's GEMINI_API_KEY for this request"
    )


class VideoSearchRequest(BaseModel):
    youtube_url: str = Field(..., min_length=1, description="A youtube.com or youtu.be video URL to search within")
    query: str = Field(..., min_length=1, description="Natural-language description of the motion to find")
    top_k: int = Field(default=5, ge=1, le=50)
    gemini_api_key: str | None = Field(
        default=None, description="Caller-supplied Gemini API key; overrides the server's GEMINI_API_KEY for this request"
    )


class SearchResultItem(BaseModel):
    video_id: str
    video_title: str | None
    thumbnail_url: str | None = None
    start_sec: float
    end_sec: float
    confidence: float
    description: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
