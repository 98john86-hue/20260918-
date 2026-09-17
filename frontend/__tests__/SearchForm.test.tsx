import { fireEvent, render, screen } from "@testing-library/react";

import SearchForm from "@/components/SearchForm";

describe("SearchForm", () => {
  it("calls onSearch with the entered query on submit", () => {
    const onSearch = jest.fn();
    render(<SearchForm onSearch={onSearch} isSearching={false} />);

    const input = screen.getByPlaceholderText("예: 자유형 턴에서 팔을 젓는 모습");
    fireEvent.change(input, { target: { value: "자유형 턴" } });
    fireEvent.submit(screen.getByRole("button", { name: "검색" }));

    expect(onSearch).toHaveBeenCalledWith("자유형 턴");
  });

  it("disables the submit button while searching", () => {
    render(<SearchForm onSearch={jest.fn()} isSearching={true} />);
    expect(screen.getByRole("button", { name: "검색 중..." })).toBeDisabled();
  });
});
