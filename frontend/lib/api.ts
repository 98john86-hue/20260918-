import type { SearchResponse, VideoItem, VideoListResponse } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `Request failed with status ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function registerVideo(youtubeUrl: string): Promise<VideoItem> {
  const res = await fetch(`${API_BASE_URL}/api/videos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ youtube_url: youtubeUrl }),
  });
  return handleResponse<VideoItem>(res);
}

export async function listVideos(): Promise<VideoListResponse> {
  const res = await fetch(`${API_BASE_URL}/api/videos`);
  return handleResponse<VideoListResponse>(res);
}

export async function searchLibrary(query: string, topK = 5): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE_URL}/api/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k: topK }),
  });
  return handleResponse<SearchResponse>(res);
}

export async function searchInVideo(youtubeUrl: string, query: string, topK = 5): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE_URL}/api/search/video`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ youtube_url: youtubeUrl, query, top_k: topK }),
  });
  return handleResponse<SearchResponse>(res);
}
