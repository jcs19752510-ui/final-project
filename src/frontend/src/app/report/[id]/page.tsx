import { ProtectedRoute } from "../../../components/ProtectedRoute";
import { ReportPage } from "../../../screens/ReportPage";

export default function Page() {
  return (
    <ProtectedRoute requireRole="candidate">
      <ReportPage />
    </ProtectedRoute>
  );
}
