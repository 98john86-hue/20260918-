export type VideoStatus = "pending" | "downloading" | "analyzing" | "completed" | "failed";

export interface VideoItem {
  id: number;
  youtube_url: string;
  video_id: string;
  title: string | null;
  thumbnail_url: string | null;
  duration_sec: number | null;
  status: VideoStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface VideoListResponse {
  videos: VideoItem[];
}

export interface SearchResultItem {
  video_id: string;
  video_title: string | null;
  thumbnail_url: string | null;
  start_sec: number;
  end_sec: number;
  confidence: number;
  description: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResultItem[];
}
