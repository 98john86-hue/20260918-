import type { SearchResultItem } from "@/lib/types";

function formatTimestamp(sec: number): string {
  const minutes = Math.floor(sec / 60);
  const seconds = Math.floor(sec % 60);
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

interface Props {
  result: SearchResultItem;
  onSelect: (result: SearchResultItem) => void;
}

export default function ResultCard({ result, onSelect }: Props) {
  const confidencePct = Math.round(result.confidence * 100);

  return (
    <button
      type="button"
      onClick={() => onSelect(result)}
      className="flex w-full gap-3 rounded-md border border-slate-200 p-3 text-left transition hover:border-sky-400 hover:shadow-sm"
    >
      {result.thumbnail_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={result.thumbnail_url} alt="" className="h-16 w-28 shrink-0 rounded object-cover" />
      ) : (
        <div className="h-16 w-28 shrink-0 rounded bg-slate-100" />
      )}
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-slate-900">{result.video_title ?? result.video_id}</p>
        <p className="text-xs text-slate-500">
          {formatTimestamp(result.start_sec)} - {formatTimestamp(result.end_sec)} · 신뢰도 {confidencePct}%
        </p>
        <p className="mt-1 line-clamp-2 text-xs text-slate-600">{result.description}</p>
      </div>
    </button>
  );
}
