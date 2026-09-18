"use client";

import { useState } from "react";

import { useVideoMotionSearch } from "@/hooks/useVideoMotionSearch";
import ResultList from "@/components/ResultList";
import VideoMotionSearchForm from "@/components/VideoMotionSearchForm";
import YouTubePlayer from "@/components/YouTubePlayer";
import type { SearchResultItem } from "@/lib/types";

export default function VideoMotionSearchPage() {
  const { results, isSearching, error, hasSearched, search } = useVideoMotionSearch();
  const [selected, setSelected] = useState<SearchResultItem | null>(null);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-lg font-semibold">영상 내 모션 검색</h1>
        <p className="mt-1 text-sm text-slate-500">
          영상 링크와 찾고 싶은 모션을 입력하면 해당 영상 안에서 일치하는 장면을 찾아드립니다.
        </p>
      </div>

      <VideoMotionSearchForm onSearch={search} isSearching={isSearching} />

      {error && <p className="text-sm text-red-600">{error}</p>}

      {selected && (
        <div>
          <YouTubePlayer videoId={selected.video_id} startSec={selected.start_sec} />
          <p className="mt-2 text-sm text-slate-600">{selected.description}</p>
        </div>
      )}

      {!error && hasSearched && <ResultList results={results} onSelect={setSelected} />}
    </div>
  );
}
