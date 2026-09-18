from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.video import Video, VideoStatus
from app.schemas.search import SearchRequest, SearchResponse, VideoSearchRequest
from app.services.llm_analysis import LLMConfigurationError, get_llm_analyzer
from app.services.search import search_in_video, search_library
from app.services.youtube import InvalidUrlError, extract_video_id

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search(payload: SearchRequest, db: Session = Depends(get_db)) -> SearchResponse:
    try:
        analyzer = get_llm_analyzer()
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    results = search_library(db, analyzer, payload.query, payload.top_k)
    return SearchResponse(query=payload.query, results=results)


@router.post("/video", response_model=SearchResponse)
def search_video(payload: VideoSearchRequest, db: Session = Depends(get_db)) -> SearchResponse:
    try:
        video_id = extract_video_id(payload.youtube_url)
    except InvalidUrlError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    video = db.query(Video).filter(Video.video_id == video_id).first()
    if video is None:
        raise HTTPException(status_code=404, detail="등록되지 않은 영상입니다. 먼저 영상을 등록해주세요.")
    if video.status != VideoStatus.COMPLETED:
        raise HTTPException(status_code=409, detail=f"영상이 아직 처리 중입니다 (상태: {video.status.value}).")

    try:
        analyzer = get_llm_analyzer()
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    results = search_in_video(analyzer, video, payload.query, payload.top_k)
    return SearchResponse(query=payload.query, results=results)
