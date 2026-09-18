"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../state/AuthContext";
import type { Role } from "../api/types";

// 2026-09-18(Next.js 전환): react-router의 <Navigate>는 렌더링 중 즉시
// 리다이렉트를 "선언"할 수 있었지만, Next.js App Router의 클라이언트
// 라우터에는 그런 선언적 컴포넌트가 없다 — router.replace()를 효과 안에서
// 호출하는 명령형 방식으로 대체(공식 문서가 권장하는 클라이언트 컴포넌트
// 리다이렉트 패턴).
export function ProtectedRoute({
  children,
  requireRole,
}: {
  children: ReactNode;
  requireRole?: Role;
}) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  if (loading) return <p className="page-loading">불러오는 중...</p>;
  if (!user) return null; // 리다이렉트가 반영되기 전의 짧은 순간
  if (requireRole && user.role !== requireRole) {
    return (
      <div className="access-denied">
        <h2>접근 권한이 없습니다</h2>
        <p>이 화면은 {requireRole === "recruiter" ? "채용담당자" : "지원자"} 전용입니다.</p>
      </div>
    );
  }
  return <>{children}</>;
}
