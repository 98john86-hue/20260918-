"""Multimodal (video) and text LLM calls, backed by the Gemini API.

Design note ("why"): a naive implementation would re-upload the full video
to the LLM on every search query. Instead we call the multimodal LLM once
per video, at registration time, to produce a cached list of `SceneSegment`s
(see analyze_video). Every subsequent search then only sends the *text*
descriptions of those cached segments plus the user's query to a much
cheaper text-only call (see rank_segments) instead of the video itself.
This keeps LLM cost roughly constant per video instead of growing with the
number of searches, per the caching requirement in the project brief.
Phase 2 replaces rank_segments' text-similarity call with a pgvector
nearest-neighbour lookup over frame embeddings; analyze_video's cached
segments remain as the human-readable fallback/explanation either way.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Protocol

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import get_settings

logger = logging.getLogger(__name__)


class TransientLLMError(Exception):
    """Raised for retryable failures (timeouts, rate limits, 5xx)."""


class LLMConfigurationError(Exception):
    """Raised when the LLM client is not configured (e.g. missing API key)."""


@dataclass
class SceneSegment:
    start_sec: float
    end_sec: float
    description: str


@dataclass
class MatchResult:
    segment_index: int
    confidence: float
    description: str


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

VIDEO_ANALYSIS_PROMPT = """You are a swimming technique analyst. Watch this swimming video carefully
and identify every notable technique moment (starts, turns, stroke cycles,
finishes, breathing patterns, underwater kicks). For each moment, output the
start and end timestamp in seconds and a short factual description.

Respond with ONLY a JSON array, no prose, matching this shape:
[
  {"start_sec": 12.0, "end_sec": 18.5, "description": "Freestyle turn: swimmer approaches the wall and begins a flip turn"},
  {"start_sec": 125.0, "end_sec": 131.0, "description": "First stroke immediately after push-off from the wall"}
]
"""


def build_segment_ranking_prompt(query: str, segments: list[dict]) -> str:
    """Example prompt for the text-only re-ranking call in rank_segments().

    `segments` is the video's cached SceneSegment list serialized as
    {"index", "start_sec", "end_sec", "description"} dicts.
    """
    segments_json = json.dumps(segments, ensure_ascii=False)
    return f"""A user is searching a swimming video library with this natural-language
query: "{query}"

Here are candidate scenes already identified in one video, as a JSON array of
{{"index", "start_sec", "end_sec", "description"}}:
{segments_json}

Return ONLY a JSON array of the scenes that plausibly match the query, most
relevant first, in this shape (omit scenes that don't match at all):
[
  {{"segment_index": 3, "confidence": 0.87, "description": "Refined one-sentence description of why this matches"}}
]
confidence must be a float between 0 and 1.
"""


def build_video_query_prompt(query: str) -> str:
    """Reference example: a *single* multimodal call combining video + query.

    Not used by the default two-stage pipeline (see module docstring), which
    prefers analyzing each video once and reusing the cached result for every
    query. This is kept as a documented alternative for a "direct mode" where
    per-video, per-query LLM calls are acceptable (e.g. a small library where
    freshness matters more than cost) — see README for usage.
    """
    return f"""You are a swimming technique analyst. Watch this swimming video and find the
moment(s) that best match this description: "{query}"

Respond with ONLY a JSON array of matches, most relevant first:
[
  {{"start_sec": 125.0, "end_sec": 131.0, "confidence": 0.87, "description": "Swimmer's first stroke right after push-off from the wall"}}
]
confidence must be a float between 0 and 1. Return an empty array if nothing matches.
"""


# ---------------------------------------------------------------------------
# Response parsing (pure functions — easy to unit test without a network call)
# ---------------------------------------------------------------------------


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    return text.strip()


def parse_scene_segments(raw_text: str) -> list[SceneSegment]:
    data = json.loads(_strip_code_fence(raw_text))
    return [
        SceneSegment(
            start_sec=float(item["start_sec"]),
            end_sec=float(item["end_sec"]),
            description=str(item["description"]),
        )
        for item in data
    ]


def parse_match_results(raw_text: str) -> list[MatchResult]:
    data = json.loads(_strip_code_fence(raw_text))
    return [
        MatchResult(
            segment_index=int(item["segment_index"]),
            confidence=float(item["confidence"]),
            description=str(item["description"]),
        )
        for item in data
    ]


# ---------------------------------------------------------------------------
# LLM client interface + Gemini implementation
# ---------------------------------------------------------------------------


class LLMAnalyzer(Protocol):
    def analyze_video(self, local_path: str) -> list[SceneSegment]: ...

    def rank_segments(self, query: str, segments: list[SceneSegment]) -> list[MatchResult]: ...


class GeminiAnalyzer:
    def __init__(self, api_key: str, model_name: str, max_retries: int, min_wait: float, max_wait: float) -> None:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self._genai = genai
        self._model = genai.GenerativeModel(model_name)
        self._retry_decorator = retry(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(TransientLLMError),
            reraise=True,
        )

    def _generate(self, parts: list) -> str:
        @self._retry_decorator
        def _call() -> str:
            try:
                response = self._model.generate_content(parts)
            except Exception as exc:  # noqa: BLE001 - map every SDK error to our taxonomy
                logger.warning("Gemini call failed, will retry if attempts remain: %s", exc)
                raise TransientLLMError(str(exc)) from exc
            if not response.text:
                raise TransientLLMError("Empty response from Gemini")
            return response.text

        return _call()

    def analyze_video(self, local_path: str) -> list[SceneSegment]:
        video_file = self._genai.upload_file(local_path)
        try:
            raw_text = self._generate([video_file, VIDEO_ANALYSIS_PROMPT])
        finally:
            self._genai.delete_file(video_file.name)
        return parse_scene_segments(raw_text)

    def rank_segments(self, query: str, segments: list[SceneSegment]) -> list[MatchResult]:
        segment_dicts = [
            {"index": i, "start_sec": s.start_sec, "end_sec": s.end_sec, "description": s.description}
            for i, s in enumerate(segments)
        ]
        prompt = build_segment_ranking_prompt(query, segment_dicts)
        raw_text = self._generate([prompt])
        return parse_match_results(raw_text)


def get_llm_analyzer() -> LLMAnalyzer:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise LLMConfigurationError(
            "GEMINI_API_KEY is not set. Configure it in .env to enable video analysis."
        )
    return GeminiAnalyzer(
        api_key=settings.gemini_api_key,
        model_name=settings.gemini_model,
        max_retries=settings.llm_max_retries,
        min_wait=settings.llm_retry_min_wait_sec,
        max_wait=settings.llm_retry_max_wait_sec,
    )
