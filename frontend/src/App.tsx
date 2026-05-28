import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { DashboardLayout } from '@/layouts/DashboardLayout';
import { PageLoading } from '@/components/common/LoadingSpinner';
import { LoginPage } from '@/pages/LoginPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { UploadCenterPage } from '@/pages/UploadCenterPage';
import { UploadHistoryPage } from '@/pages/UploadHistoryPage';
import { ReviewQueuePage } from '@/pages/ReviewQueuePage';
import { SuspiciousRecordsPage } from '@/pages/SuspiciousRecordsPage';
import { EmissionsExplorerPage } from '@/pages/EmissionsExplorerPage';
import { AuditTimelinePage } from '@/pages/AuditTimelinePage';
import { RecordDetailsPage } from '@/pages/RecordDetailsPage';
import { UploadSessionDetailPage } from '@/pages/UploadSessionDetailPage';

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <PageLoading />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function RedirectIfAuthenticated({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <PageLoading />;
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <RedirectIfAuthenticated>
            <LoginPage />
          </RedirectIfAuthenticated>
        }
      />
      <Route
        element={
          <RequireAuth>
            <DashboardLayout />
          </RequireAuth>
        }
      >
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/uploads" element={<UploadCenterPage />} />
        <Route path="/uploads/history" element={<UploadHistoryPage />} />
        <Route path="/uploads/:sessionId" element={<UploadSessionDetailPage />} />
        <Route path="/reviews" element={<ReviewQueuePage />} />
        <Route path="/suspicious" element={<SuspiciousRecordsPage />} />
        <Route path="/emissions" element={<EmissionsExplorerPage />} />
        <Route path="/emissions/:recordId" element={<RecordDetailsPage />} />
        <Route path="/audit" element={<AuditTimelinePage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
