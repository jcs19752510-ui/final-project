import { ProtectedRoute } from "../components/ProtectedRoute";
import { CandidateHomePage } from "../screens/CandidateHomePage";

export default function Page() {
  return (
    <ProtectedRoute requireRole="candidate">
      <CandidateHomePage />
    </ProtectedRoute>
  );
}
