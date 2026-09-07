import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../state/AuthContext";
import type { Role } from "../api/types";

export function ProtectedRoute({
  children,
  requireRole,
}: {
  children: ReactNode;
  requireRole?: Role;
}) {
  const { user, loading } = useAuth();

  if (loading) return <p className="page-loading">불러오는 중...</p>;
  if (!user) return <Navigate to="/login" replace />;
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
