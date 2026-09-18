"use client";

import { useVideoLibrary } from "@/hooks/useVideoLibrary";
import VideoLibraryList from "@/components/VideoLibraryList";
import VideoRegisterForm from "@/components/VideoRegisterForm";

export default function RegisterPage() {
  const { videos, isLoading, isRegistering, error, register } = useVideoLibrary();

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-lg font-semibold">유튜브 영상 등록</h1>
        <p className="mt-1 text-sm text-slate-500">
          등록된 영상은 자동으로 다운로드 및 분석되며, 완료되면 검색 대상에 포함됩니다. 1시간이 넘는 긴
          영상은 처리 시간과 분석 비용이 커질 수 있습니다.
        </p>
      </div>

      <VideoRegisterForm onSubmit={register} isSubmitting={isRegistering} />

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div>
        <h2 className="mb-2 text-sm font-semibold text-slate-700">등록된 영상 라이브러리</h2>
        {isLoading ? <p className="text-sm text-slate-500">불러오는 중...</p> : <VideoLibraryList videos={videos} />}
      </div>
    </div>
  );
}
