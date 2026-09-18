"use client";

import { useCallback, useState } from "react";

import { searchLibrary } from "@/lib/api";
import type { SearchResultItem } from "@/lib/types";

export function useSearch() {
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastQuery, setLastQuery] = useState<string | null>(null);

  const search = useCallback(async (query: string) => {
    if (!query.trim()) return;
    setIsSearching(true);
    setError(null);
    try {
      const response = await searchLibrary(query);
      setResults(response.results);
      setLastQuery(response.query);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  return { results, isSearching, error, lastQuery, search };
}
