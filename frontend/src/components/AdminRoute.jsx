import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * AdminRoute — Solo permite acceso a usuarios con rol 'admin'.
 * Cualquier otro usuario autenticado es redirigido al Dashboard.
 * Usuarios no autenticados son redirigidos al Login.
 */
export default function AdminRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Cargando...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (user.role !== 'admin') {
    // Usuario autenticado pero sin permisos → redirigir al Dashboard
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}
