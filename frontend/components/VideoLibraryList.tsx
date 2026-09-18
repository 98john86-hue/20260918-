import type { VideoItem, VideoStatus } from "@/lib/types";

const STATUS_LABEL: Record<VideoStatus, string> = {
  pending: "대기",
  downloading: "다운로드중",
  analyzing: "분석중",
  completed: "완료",
  failed: "실패",
};

const STATUS_COLOR: Record<VideoStatus, string> = {
  pending: "bg-slate-100 text-slate-700",
  downloading: "bg-amber-100 text-amber-700",
  analyzing: "bg-amber-100 text-amber-700",
  completed: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
};

function formatDuration(sec: number | null): string {
  if (sec === null) return "-";
  const minutes = Math.floor(sec / 60);
  const seconds = sec % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

export default function VideoLibraryList({ videos }: { videos: VideoItem[] }) {
  if (videos.length === 0) {
    return <p className="text-sm text-slate-500">등록된 영상이 없습니다. 위에서 유튜브 URL을 등록해 보세요.</p>;
  }

  return (
    <ul className="divide-y divide-slate-200 rounded-md border border-slate-200">
      {videos.map((video) => (
        <li key={video.id} className="flex items-center gap-3 p-3">
          {video.thumbnail_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={video.thumbnail_url} alt="" className="h-12 w-20 rounded object-cover" />
          ) : (
            <div className="h-12 w-20 rounded bg-slate-100" />
          )}
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-slate-900">{video.title ?? video.youtube_url}</p>
            <p className="text-xs text-slate-500">{formatDuration(video.duration_sec)}</p>
            {video.status === "failed" && video.error_message && (
              <p className="mt-1 text-xs text-red-600">{video.error_message}</p>
            )}
          </div>
          <span className={`rounded-full px-2 py-1 text-xs font-medium ${STATUS_COLOR[video.status]}`}>
            {STATUS_LABEL[video.status]}
          </span>
        </li>
      ))}
    </ul>
  );
}
