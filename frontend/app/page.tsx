import Link from "next/link";

export default function HomePage() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold">수영 장면 검색</h1>
      <p className="text-sm text-slate-600">
        유튜브 수영 영상을 등록하고, 원하는 장면을 자연어로 검색해 보세요.
      </p>
      <div className="flex gap-4">
        <Link href="/register" className="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white">
          영상 등록하기
        </Link>
        <Link href="/search" className="rounded-md border border-sky-600 px-4 py-2 text-sm font-medium text-sky-600">
          장면 검색하기
        </Link>
      </div>
    </div>
  );
}
