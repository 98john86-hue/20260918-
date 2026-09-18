# Swim Scene Search

유튜브 링크로 등록한 여러 수영 영상 중에서, 자연어로 설명한 장면(예: "자유형 턴에서 팔을 젓는 모습")과 가장 유사한
순간을 자동으로 찾아 타임스탬프와 함께 보여주는 웹 애플리케이션입니다.

> ⚠️ **법적/윤리적 고지**: 이 프로젝트는 `yt-dlp`로 유튜브 영상을 다운로드합니다. 이는 **개인적·비상업적
> 학습 및 기술 분석 목적**으로만 사용해야 하며, 유튜브 서비스 약관과 충돌할 수 있습니다. 다운로드한 영상
> 파일을 재배포하거나 이 프로젝트를 공개 서비스로 전환하려는 경우, 반드시 별도의 법적 검토를 거치세요.

## 아키텍처 개요 (Phase 1)

```
[Next.js Frontend]  --REST-->  [FastAPI Backend]  --yt-dlp-->  YouTube
     |register/search view          |                              |
     |                              +--BackgroundTasks--> download -> analyze
     |                              |
     |                         [PostgreSQL] <-- video metadata, status, cached scene segments
     |                              |
     +<---- polling / search -------+--Gemini API (multimodal)--> scene understanding
```

**왜 두 단계 분석인가?** 영상을 등록할 때 딱 한 번 멀티모달 LLM(Gemini)에 전체 영상을 보내 장면별
타임스탬프+설명을 뽑아 `analysis_segments` 테이블에 캐시합니다. 검색 시에는 이 캐시된 설명 텍스트와
사용자 쿼리만 텍스트 LLM 호출로 비교합니다. 즉, 영상은 등록 시 1회만 업로드되고, 이후 검색 횟수와
무관하게 LLM 비용이 늘어나지 않습니다. (Phase 2에서는 이 텍스트 매칭을 프레임 임베딩 벡터 검색으로
대체할 예정이며, `app/services/search.py`의 인터페이스만 교체하면 됩니다.)

## 디렉토리 구조

```
backend/
  app/
    api/            # FastAPI 라우터 (videos, search)
    models/         # SQLAlchemy 모델 (Video, AnalysisSegment)
    schemas/        # Pydantic 요청/응답 스키마
    services/       # yt-dlp 다운로드, Gemini 분석, 검색 매칭 로직
    workers/        # 백그라운드 작업 엔트리포인트 (BackgroundTasks -> 추후 Celery)
    config.py, database.py, main.py
  tests/            # pytest 유닛/통합 테스트 (외부 API는 mock)
frontend/
  app/
    register/       # "URL 등록" 화면
    search/         # "검색 + 결과" 화면
  components/       # VideoRegisterForm, VideoLibraryList, SearchForm, ResultList, ResultCard, YouTubePlayer
  hooks/            # useVideoLibrary(등록+폴링), useSearch
  lib/               # api.ts(fetch 클라이언트), types.ts
  __tests__/        # 컴포넌트 테스트 (Testing Library)
docker-compose.yml
```

## 로컬 실행 (Docker Compose)

```bash
cp backend/.env.example backend/.env    # GEMINI_API_KEY 입력
cp frontend/.env.example frontend/.env.local

docker compose up --build
# frontend: http://localhost:3000
# backend:  http://localhost:8000/health
```

### 로컬에서 직접 실행 (Docker 없이)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # DATABASE_URL을 로컬 Postgres에 맞게 수정
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## 테스트

```bash
# Backend (yt-dlp, Gemini API는 모두 mock 처리)
cd backend && pytest

# Frontend
cd frontend && npm test
```

## API

### `POST /api/videos` — 유튜브 URL 등록

같은 `video_id`가 이미 `completed` 상태로 등록되어 있으면 재다운로드/재분석 없이 기존 레코드를 반환합니다.

```json
{ "youtube_url": "https://www.youtube.com/watch?v=abc12345678" }
```

### `GET /api/videos` — 라이브러리 조회 (프론트에서 상태 폴링에 사용)

상태 값: `pending` → `downloading` → `analyzing` → `completed` | `failed`

### `POST /api/search` — 자연어 장면 검색

```json
{ "query": "자유형 턴에서 팔을 젓는 모습", "top_k": 5 }
```

응답:

```json
{
  "query": "자유형 턴에서 팔을 젓는 모습",
  "results": [
    {
      "video_id": "abc123",
      "video_title": "Olympic Freestyle Technique",
      "start_sec": 125,
      "end_sec": 131,
      "confidence": 0.87,
      "description": "선수가 벽을 차고 나온 직후 첫 스트로크 장면"
    }
  ]
}
```

## 참고 예시

### yt-dlp 기본 다운로드 커맨드

```bash
yt-dlp -f "mp4/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best" \
  -o "downloads/%(id)s.%(ext)s" \
  "https://www.youtube.com/watch?v=abc12345678"
```

(`app/services/youtube.py`의 `download_video()`가 동일한 옵션을 파이썬 API로 호출합니다.)

### 멀티모달 LLM 분석 프롬프트 (영상 등록 시, `app/services/llm_analysis.py`)

```
You are a swimming technique analyst. Watch this swimming video carefully
and identify every notable technique moment (starts, turns, stroke cycles,
finishes, breathing patterns, underwater kicks). For each moment, output the
start and end timestamp in seconds and a short factual description.

Respond with ONLY a JSON array, no prose, matching this shape:
[
  {"start_sec": 12.0, "end_sec": 18.5, "description": "Freestyle turn: swimmer approaches the wall and begins a flip turn"}
]
```

### 영상+텍스트 쿼리를 함께 보내는 대안 프롬프트 (참고용, `build_video_query_prompt`)

비용 효율을 위해 기본 파이프라인은 사용하지 않지만, 라이브러리가 작고 매번 최신 상태로 재분석하고 싶을 때
쓸 수 있는 "직접 모드" 예시로 남겨두었습니다.

```
You are a swimming technique analyst. Watch this swimming video and find the
moment(s) that best match this description: "{query}"

Respond with ONLY a JSON array of matches, most relevant first:
[
  {"start_sec": 125.0, "end_sec": 131.0, "confidence": 0.87, "description": "Swimmer's first stroke right after push-off from the wall"}
]
```

### 유튜브 iframe API로 특정 시점부터 재생 (`components/YouTubePlayer.tsx`)

```ts
// player.seekTo(seconds, true) — 두 번째 인자 true는 가장 가까운 키프레임을
// 기다리지 않고 정확한 지점으로 강제 탐색하도록 지시합니다.
player.loadVideoById({ videoId: "abc123", startSeconds: 125 });
// 같은 영상 내에서 다른 구간으로 이동할 때는:
player.seekTo(125, true);
```

## 제약사항

- 비공개/연령제한/삭제된 영상은 다운로드 단계에서 명확한 에러 메시지로 실패 처리됩니다
  (`app/services/youtube.py`의 `PrivateVideoError`, `AgeRestrictedVideoError`, `VideoUnavailableError`).
- 기본적으로 1시간(3600초)을 초과하는 영상은 등록이 거부됩니다 (`MAX_VIDEO_DURATION_SEC` 환경변수로 조정).
  프론트엔드 등록 화면에도 긴 영상에 대한 경고 문구가 표시됩니다.
- Gemini API 호출은 실패 시 지수 백오프로 최대 4회까지 재시도합니다 (`tenacity`, `LLM_MAX_RETRIES`).
- API 키 등 민감 정보는 `.env` 파일로만 관리하며 `.gitignore`에 포함되어 커밋되지 않습니다.

## Phase 2 로드맵 (인터페이스만 반영, 미구현)

- `AnalysisSegment`에 프레임 임베딩(CLIP/SigLIP) 컬럼 추가 + pgvector 기반 유사도 검색으로
  `app/services/search.py` 교체
- 검색 결과 재검증을 위한 2차 LLM re-rank 단계
- 수영 종목(`stroke_type`)·구간(`phase`) 필터/태깅 (모델에 이미 placeholder 컬럼 존재)
- 사용자 인증 및 개인별 라이브러리/검색 기록
- FastAPI BackgroundTasks → Celery + Redis 전환 (`app/workers/tasks.py`가 이미 서비스 로직과
  분리되어 있어 `@celery_app.task`로 감싸기만 하면 됨)
