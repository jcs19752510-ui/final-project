import { Link, Route, Routes } from "react-router-dom";
import { useAuth } from "./state/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { LoginPage } from "./pages/LoginPage";
import { SignupPage } from "./pages/SignupPage";
import { CandidateHomePage } from "./pages/CandidateHomePage";
import { InterviewPage } from "./pages/InterviewPage";
import { CodingPage } from "./pages/CodingPage";
import { ReportPage } from "./pages/ReportPage";
import { DashboardPage } from "./pages/DashboardPage";
import { RecruiterReportPage } from "./pages/RecruiterReportPage";

function NavBar() {
  const { user, logout } = useAuth();
  return (
    <header className="nav-bar">
      <Link to="/" className="brand">
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

export default function App() {
  return (
    <>
      <NavBar />
      <main>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute requireRole="candidate">
                <CandidateHomePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/interview/:id"
            element={
              <ProtectedRoute requireRole="candidate">
                <InterviewPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/interview/:id/coding"
            element={
              <ProtectedRoute requireRole="candidate">
                <CodingPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/report/:id"
            element={
              <ProtectedRoute requireRole="candidate">
                <ReportPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute requireRole="recruiter">
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard/report/:id"
            element={
              <ProtectedRoute requireRole="recruiter">
                <RecruiterReportPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
    </>
  );
}
