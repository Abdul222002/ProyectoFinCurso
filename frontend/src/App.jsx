import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import AdminRoute from './components/AdminRoute';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import Dashboard from './pages/Dashboard';
import TeamManagementPage from './pages/TeamManagementPage';
import MarketPage from './pages/MarketPage';
import ArenaPage from './pages/ArenaPage';
import CardDetailPage from './pages/CardDetailPage';
import PriceAnalysisPage from './pages/PriceAnalysisPage';
import LeaguesPage from './pages/LeaguesPage';
import LeagueDetailPage from './pages/LeagueDetailPage';
import AdminDashboard from './pages/AdminDashboard';
import ProfilePage from './pages/ProfilePage';
import CookiesPage from './pages/CookiesPage';
import VerifyEmailPage from './pages/VerifyEmailPage';
import PendingVerificationPage from './pages/PendingVerificationPage';
import CookieBanner from './components/CookieBanner';

function App() {
  return (
    <AuthProvider>
      <Toaster theme="dark" position="bottom-center" richColors />
      <Router>
        <Routes>
          {/* Rutas públicas */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/verify-email" element={<VerifyEmailPage />} />
          <Route path="/pending-verification" element={<PendingVerificationPage />} />
          <Route path="/cookies" element={<CookiesPage />} />

          {/* Rutas protegidas */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/team"
            element={
              <ProtectedRoute>
                <TeamManagementPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/market"
            element={
              <ProtectedRoute>
                <MarketPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/arena"
            element={
              <ProtectedRoute>
                <ArenaPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/player/:playerId"
            element={
              <ProtectedRoute>
                <CardDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/analysis/:playerId"
            element={
              <ProtectedRoute>
                <PriceAnalysisPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/leagues"
            element={
              <ProtectedRoute>
                <LeaguesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/leagues/:leagueId"
            element={
              <ProtectedRoute>
                <LeagueDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <AdminDashboard />
              </AdminRoute>
            }
          />

          {/* Redirección por defecto */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
        <CookieBanner />
      </Router>
    </AuthProvider>
  );
}

export default App;
