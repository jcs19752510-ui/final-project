"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { AuthProvider, useAuth } from "../state/AuthContext";

// 2026-09-18(Next.js 전환): 예전 App.tsx의 <NavBar/> + <Routes>를 감싸던
// 구조를 대체 — 루트 레이아웃(app/layout.tsx, Server Component)은 얇게
// 유지하고, 인증 상태를 쓰는 실제 UI는 이 Client Component가 담당한다.
function NavBar() {
  const { user, logout } = useAuth();
  return (
    <header className="nav-bar">
      <Link href="/" className="brand">
        aimock
      </Link>
      {user && (
        <div className="nav-right">
          <span>{user.email}</span>
          <button onClick={logout}>로그아웃</button>
        </div>
      )}
    </header>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <NavBar />
      <main>{children}</main>
    </AuthProvider>
  );
}
