import { fireEvent, render, screen } from "@testing-library/react";

import VideoMotionSearchForm from "@/components/VideoMotionSearchForm";

describe("VideoMotionSearchForm", () => {
  it("calls onSearch with the entered url, motion, and api key on submit", () => {
    const onSearch = jest.fn();
    render(<VideoMotionSearchForm onSearch={onSearch} isSearching={false} />);

    fireEvent.change(screen.getByLabelText("영상 링크"), {
      target: { value: "https://www.youtube.com/watch?v=abc123" },
    });
    fireEvent.change(screen.getByLabelText("원하는 모션"), {
      target: { value: "자유형 턴" },
    });
    fireEvent.change(screen.getByLabelText("Gemini API 키"), {
      target: { value: "test-api-key" },
    });
    fireEvent.submit(screen.getByRole("button", { name: "검색" }));

    expect(onSearch).toHaveBeenCalledWith(
      "https://www.youtube.com/watch?v=abc123",
      "자유형 턴",
      "test-api-key"
    );
  });

  it("disables the submit button while searching", () => {
    render(<VideoMotionSearchForm onSearch={jest.fn()} isSearching={true} />);
    expect(screen.getByRole("button", { name: "검색 중..." })).toBeDisabled();
  });
});
