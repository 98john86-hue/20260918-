"use client";

import { useState } from "react";

import { useSearch } from "@/hooks/useSearch";
import ResultList from "@/components/ResultList";
import SearchForm from "@/components/SearchForm";
import YouTubePlayer from "@/components/YouTubePlayer";
import type { SearchResultItem } from "@/lib/types";

export default function SearchPage() {
  const { results, isSearching, error, lastQuery, search } = useSearch();
  const [selected, setSelected] = useState<SearchResultItem | null>(null);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-lg font-semibold">장면 검색</h1>
        <p className="mt-1 text-sm text-slate-500">
          찾고 싶은 장면을 자연어로 설명하면 등록된 영상 라이브러리 전체에서 가장 유사한 구간을 찾아드립니다.
        </p>
      </div>

      <SearchForm onSearch={search} isSearching={isSearching} />

      {error && <p className="text-sm text-red-600">{error}</p>}

      {selected && (
        <div>
          <YouTubePlayer videoId={selected.video_id} startSec={selected.start_sec} />
          <p className="mt-2 text-sm text-slate-600">{selected.description}</p>
        </div>
      )}

      <div className="grid gap-6 sm:grid-cols-2">
        <div>
          {lastQuery && <h2 className="mb-2 text-sm font-semibold text-slate-700">&ldquo;{lastQuery}&rdquo; 검색 결과</h2>}
          <ResultList results={results} onSelect={setSelected} />
        </div>
      </div>
    </div>
  );
}
