"use client";

import { FormEvent, useState } from "react";

interface Props {
  onSearch: (query: string) => void;
  isSearching: boolean;
}

export default function SearchForm({ onSearch, isSearching }: Props) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSearch(query);
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2 sm:flex-row" aria-label="search-form">
      <input
        type="text"
        required
        placeholder="예: 자유형 턴에서 팔을 젓는 모습"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none"
      />
      <button
        type="submit"
        disabled={isSearching}
        className="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {isSearching ? "검색 중..." : "검색"}
      </button>
    </form>
  );
}
