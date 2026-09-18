import { ProtectedRoute } from "../../../../components/ProtectedRoute";
import { WhiteboardPage } from "../../../../screens/WhiteboardPage";

export default function Page() {
  return (
    <ProtectedRoute requireRole="candidate">
      <WhiteboardPage />
    </ProtectedRoute>
  );
}
