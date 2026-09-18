import { ProtectedRoute } from "../../../../components/ProtectedRoute";
import { RecruiterReportPage } from "../../../../screens/RecruiterReportPage";

export default function Page() {
  return (
    <ProtectedRoute requireRole="recruiter">
      <RecruiterReportPage />
    </ProtectedRoute>
  );
}
