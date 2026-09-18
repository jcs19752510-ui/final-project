import { ProtectedRoute } from "../../components/ProtectedRoute";
import { DashboardPage } from "../../screens/DashboardPage";

export default function Page() {
  return (
    <ProtectedRoute requireRole="recruiter">
      <DashboardPage />
    </ProtectedRoute>
  );
}
