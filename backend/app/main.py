from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import search, videos
from app.config import get_settings
from app.database import Base, engine

settings = get_settings()

# MVP: create tables on startup instead of running Alembic migrations.
# Swap for a migration tool before this goes anywhere near production data.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Swim Scene Search API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(videos.router)
app.include_router(search.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
