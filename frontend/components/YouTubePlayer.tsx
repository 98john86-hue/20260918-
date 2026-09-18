"use client";

import { useEffect, useRef } from "react";

// Narrow shape of the bits of the YouTube IFrame API we actually use.
// (The full type definitions live in @types/youtube; skipped here to avoid
// an extra dependency for an MVP.)
interface YTPlayer {
  loadVideoById(options: { videoId: string; startSeconds: number }): void;
  seekTo(seconds: number, allowSeekAhead: boolean): void;
  destroy(): void;
}

declare global {
  interface Window {
    YT?: {
      Player: new (
        elementId: string,
        options: {
          videoId: string;
          playerVars?: Record<string, number>;
          events?: { onReady?: () => void };
        }
      ) => YTPlayer;
    };
    onYouTubeIframeAPIReady?: () => void;
  }
}

const CONTAINER_ID = "youtube-player-container";
let apiLoadPromise: Promise<void> | null = null;

function loadYouTubeIframeApi(): Promise<void> {
  if (typeof window === "undefined") return Promise.resolve();
  if (window.YT) return Promise.resolve();
  if (apiLoadPromise) return apiLoadPromise;

  apiLoadPromise = new Promise((resolve) => {
    window.onYouTubeIframeAPIReady = () => resolve();
    const script = document.createElement("script");
    script.src = "https://www.youtube.com/iframe_api";
    document.body.appendChild(script);
  });
  return apiLoadPromise;
}

interface Props {
  videoId: string | null;
  startSec: number | null;
}

export default function YouTubePlayer({ videoId, startSec }: Props) {
  const playerRef = useRef<YTPlayer | null>(null);
  const pendingRef = useRef<{ videoId: string; startSec: number } | null>(null);

  useEffect(() => {
    let cancelled = false;

    loadYouTubeIframeApi().then(() => {
      if (cancelled || !window.YT || playerRef.current) return;
      playerRef.current = new window.YT.Player(CONTAINER_ID, {
        videoId: videoId ?? "",
        playerVars: { autoplay: 0 },
        events: {
          onReady: () => {
            if (pendingRef.current) {
              const { videoId: pendingId, startSec: pendingStart } = pendingRef.current;
              playerRef.current?.loadVideoById({ videoId: pendingId, startSeconds: pendingStart });
              pendingRef.current = null;
            }
          },
        },
      });
    });

    return () => {
      cancelled = true;
      playerRef.current?.destroy();
      playerRef.current = null;
    };
    // Player is created once; subsequent videoId/startSec changes are handled
    // by the effect below via loadVideoById/seekTo instead of recreating it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (videoId === null || startSec === null) return;
    if (playerRef.current) {
      // player.seekTo(seconds, true) — the `true` forces YouTube to seek to
      // the exact frame instead of waiting for the next keyframe.
      playerRef.current.loadVideoById({ videoId, startSeconds: startSec });
    } else {
      pendingRef.current = { videoId, startSec };
    }
  }, [videoId, startSec]);

  return (
    <div className="aspect-video w-full overflow-hidden rounded-md bg-black">
      <div id={CONTAINER_ID} className="h-full w-full" />
    </div>
  );
}
