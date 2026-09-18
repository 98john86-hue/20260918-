import type { SearchResultItem } from "@/lib/types";

import ResultCard from "./ResultCard";

interface Props {
  results: SearchResultItem[];
  onSelect: (result: SearchResultItem) => void;
}

export default function ResultList({ results, onSelect }: Props) {
  if (results.length === 0) {
    return <p className="text-sm text-slate-500">검색 결과가 없습니다.</p>;
  }

  return (
    <ul className="flex flex-col gap-2" aria-label="search-results">
      {results.map((result, index) => (
        <li key={`${result.video_id}-${result.start_sec}-${index}`}>
          <ResultCard result={result} onSelect={onSelect} />
        </li>
      ))}
    </ul>
  );
}
