"use client";

import { FormEvent, useState } from "react";

interface Props {
  onSearch: (youtubeUrl: string, motion: string, geminiApiKey: string) => void;
  isSearching: boolean;
}

export default function VideoMotionSearchForm({ onSearch, isSearching }: Props) {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [motion, setMotion] = useState("");
  const [geminiApiKey, setGeminiApiKey] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSearch(youtubeUrl, motion, geminiApiKey);
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3" aria-label="video-motion-search-form">
      <div>
        <label htmlFor="youtube-url" className="mb-1 block text-sm font-medium text-slate-700">
          영상 링크
        </label>
        <input
          id="youtube-url"
          type="url"
          required
          placeholder="https://www.youtube.com/watch?v=..."
          value={youtubeUrl}
          onChange={(e) => setYoutubeUrl(e.target.value)}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none"
        />
      </div>
      <div>
        <label htmlFor="motion-query" className="mb-1 block text-sm font-medium text-slate-700">
          원하는 모션
        </label>
        <input
          id="motion-query"
          type="text"
          required
          placeholder="예: 자유형 턴에서 팔을 젓는 모습"
          value={motion}
          onChange={(e) => setMotion(e.target.value)}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none"
        />
      </div>
      <div>
        <label htmlFor="gemini-api-key" className="mb-1 block text-sm font-medium text-slate-700">
          Gemini API 키
        </label>
        <input
          id="gemini-api-key"
          type="password"
          required
          autoComplete="off"
          placeholder="AIza..."
          value={geminiApiKey}
          onChange={(e) => setGeminiApiKey(e.target.value)}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none"
        />
        <p className="mt-1 text-xs text-slate-500">
          본인의 Gemini API 키로 검색합니다. 서버에는 저장되지 않으며 이 요청에만 사용됩니다.
        </p>
      </div>
      <button
        type="submit"
        disabled={isSearching}
        className="self-start rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {isSearching ? "검색 중..." : "검색"}
      </button>
    </form>
  );
}
