"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { listVideos, registerVideo } from "@/lib/api";
import type { VideoItem } from "@/lib/types";

const IN_PROGRESS_STATUSES = new Set(["pending", "downloading", "analyzing"]);
const POLL_INTERVAL_MS = 3000;

export function useVideoLibrary() {
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRegistering, setIsRegistering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const refresh = useCallback(async () => {
    try {
      const { videos: fetched } = await listVideos();
      setVideos(fetched);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load videos");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Poll while any video is still being downloaded/analyzed, since Phase 1
  // uses simple client polling instead of websockets/SSE.
  useEffect(() => {
    const hasInFlight = videos.some((v) => IN_PROGRESS_STATUSES.has(v.status));
    if (hasInFlight && !pollTimer.current) {
      pollTimer.current = setInterval(refresh, POLL_INTERVAL_MS);
    } else if (!hasInFlight && pollTimer.current) {
      clearInterval(pollTimer.current);
      pollTimer.current = null;
    }
    return () => {
      if (pollTimer.current) {
        clearInterval(pollTimer.current);
        pollTimer.current = null;
      }
    };
  }, [videos, refresh]);

  const register = useCallback(
    async (youtubeUrl: string) => {
      setIsRegistering(true);
      setError(null);
      try {
        await registerVideo(youtubeUrl);
        await refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to register video");
        throw err;
      } finally {
        setIsRegistering(false);
      }
    },
    [refresh]
  );

  return { videos, isLoading, isRegistering, error, register, refresh };
}
