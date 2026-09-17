import { fireEvent, render, screen } from "@testing-library/react";

import ResultList from "@/components/ResultList";
import type { SearchResultItem } from "@/lib/types";

const sampleResults: SearchResultItem[] = [
  {
    video_id: "abc123",
    video_title: "Olympic Freestyle Technique",
    thumbnail_url: null,
    start_sec: 125,
    end_sec: 131,
    confidence: 0.87,
    description: "선수가 벽을 차고 나온 직후 첫 스트로크 장면",
  },
];

describe("ResultList", () => {
  it("renders an empty state message when there are no results", () => {
    render(<ResultList results={[]} onSelect={jest.fn()} />);
    expect(screen.getByText("검색 결과가 없습니다.")).toBeInTheDocument();
  });

  it("renders a card per result and reports the confidence percentage", () => {
    render(<ResultList results={sampleResults} onSelect={jest.fn()} />);
    expect(screen.getByText("Olympic Freestyle Technique")).toBeInTheDocument();
    expect(screen.getByText(/신뢰도 87%/)).toBeInTheDocument();
  });

  it("calls onSelect with the clicked result", () => {
    const onSelect = jest.fn();
    render(<ResultList results={sampleResults} onSelect={onSelect} />);
    fireEvent.click(screen.getByText("Olympic Freestyle Technique"));
    expect(onSelect).toHaveBeenCalledWith(sampleResults[0]);
  });
});
