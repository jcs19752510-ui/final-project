import { ProtectedRoute } from "../../../../components/ProtectedRoute";
import { CodingPage } from "../../../../screens/CodingPage";

export default function Page() {
  return (
    <ProtectedRoute requireRole="candidate">
      <CodingPage />
    </ProtectedRoute>
  );
}
