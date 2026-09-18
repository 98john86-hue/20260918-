"use client";

import { useCallback, useState } from "react";

import { searchInVideo } from "@/lib/api";
import type { SearchResultItem } from "@/lib/types";

export function useVideoMotionSearch() {
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const search = useCallback(async (youtubeUrl: string, query: string, geminiApiKey: string) => {
    if (!youtubeUrl.trim() || !query.trim() || !geminiApiKey.trim()) return;
    setIsSearching(true);
    setError(null);
    try {
      const response = await searchInVideo(youtubeUrl.trim(), query.trim(), geminiApiKey.trim());
      setResults(response.results);
      setHasSearched(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "검색에 실패했습니다.");
      setResults([]);
      setHasSearched(true);
    } finally {
      setIsSearching(false);
    }
  }, []);

  return { results, isSearching, error, hasSearched, search };
}
