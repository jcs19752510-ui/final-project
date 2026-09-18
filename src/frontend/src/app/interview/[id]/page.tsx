import { ProtectedRoute } from "../../../components/ProtectedRoute";
import { InterviewPage } from "../../../screens/InterviewPage";

export default function Page() {
  return (
    <ProtectedRoute requireRole="candidate">
      <InterviewPage />
    </ProtectedRoute>
  );
}
