from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.search import SearchRequest, SearchResponse
from app.services.llm_analysis import LLMConfigurationError, get_llm_analyzer
from app.services.search import search_library

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search(payload: SearchRequest, db: Session = Depends(get_db)) -> SearchResponse:
    try:
        analyzer = get_llm_analyzer()
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    results = search_library(db, analyzer, payload.query, payload.top_k)
    return SearchResponse(query=payload.query, results=results)
