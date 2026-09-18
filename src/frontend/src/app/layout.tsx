import type { Metadata } from "next";
import type { ReactNode } from "react";
import "../index.css";
import { AppShell } from "../components/AppShell";

export const metadata: Metadata = {
  title: "aimock",
  icons: { icon: "/favicon.svg" },
};

// Server Component로 유지 — metadata export를 위해. 실제 인터랙티브 UI
// (인증 상태, 네비게이션)는 AppShell(Client Component)에 위임한다.
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
