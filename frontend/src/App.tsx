import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from '@/auth/AuthProvider';
import { RequireAuth } from '@/auth/RequireAuth';
import { AppLayout } from '@/components/AppLayout';
import { PageSpinner } from '@/components/States';

const LoginPage = lazy(() => import('@/pages/Login'));
const EmployeesPage = lazy(() => import('@/pages/employees/EmployeesPage'));
const ProjectsPage = lazy(() => import('@/pages/projects/ProjectsPage'));
const OccupancyPage = lazy(() => import('@/pages/occupancy/OccupancyPage'));
const AuditPage = lazy(() => import('@/pages/audit/AuditPage'));
const NotFoundPage = lazy(() => import('@/pages/NotFound'));

export default function App() {
  return (
    <AuthProvider>
      <Suspense fallback={<PageSpinner />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <RequireAuth>
                <AppLayout />
              </RequireAuth>
            }
          >
            <Route index element={<Navigate to="/occupancy" replace />} />
            <Route path="employees" element={<EmployeesPage />} />
            <Route path="projects" element={<ProjectsPage />} />
            <Route path="occupancy" element={<OccupancyPage />} />
            <Route path="audit" element={<AuditPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </Suspense>
    </AuthProvider>
  );
}