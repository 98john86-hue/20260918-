import type { Metadata } from "next";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "Swim Scene Search",
  description: "자연어로 수영 영상 속 장면을 검색합니다",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="min-h-screen text-slate-900">
        <header className="border-b border-slate-200 bg-white">
          <nav className="mx-auto flex max-w-4xl items-center gap-6 px-4 py-3">
            <span className="font-semibold">Swim Scene Search</span>
            <Link href="/register" className="text-sm text-slate-600 hover:text-sky-600">
              영상 등록
            </Link>
            <Link href="/search" className="text-sm text-slate-600 hover:text-sky-600">
              장면 검색
            </Link>
          </nav>
        </header>
        <main className="mx-auto max-w-4xl px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
