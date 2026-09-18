"use client";

import { FormEvent, useState } from "react";

interface Props {
  onSubmit: (youtubeUrl: string) => Promise<void>;
  isSubmitting: boolean;
}

export default function VideoRegisterForm({ onSubmit, isSubmitting }: Props) {
  const [url, setUrl] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    await onSubmit(url.trim());
    setUrl("");
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2 sm:flex-row" aria-label="video-register-form">
      <input
        type="url"
        required
        placeholder="https://www.youtube.com/watch?v=..."
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none"
      />
      <button
        type="submit"
        disabled={isSubmitting}
        className="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {isSubmitting ? "등록 중..." : "등록"}
      </button>
    </form>
  );
}
