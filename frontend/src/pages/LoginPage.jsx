import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './AuthPages.css';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      // 403 = email no verificado → redirigir a la pantalla de verificación OTP
      if (err.response?.status === 403) {
        navigate(`/verify-email?email=${encodeURIComponent(email)}`);
        return;
      }
      setError(err.response?.data?.detail || 'Credenciales incorrectas. Revisa tu email y contraseña.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      {/* ─── LEFT — Brand Panel ─── */}
      <div className="auth-left">
        <div className="auth-left__bg">
          <div className="auth-left__orb auth-left__orb--1" />
          <div className="auth-left__orb auth-left__orb--2" />
        </div>
        <div className="auth-left__content">
          <div className="auth-left__badge">🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Premiership</div>
          <div className="auth-left__logo-wrap">
            <img src="/logo-premium.png" alt="UFL Logo" />
          </div>
          <h1 className="auth-left__title">Ultimate Fantasy<br /><span>Legends</span></h1>
          <p className="auth-left__desc">
            Construye tu equipo ideal, ficha estrellas en el mercado y compite en ligas privadas con tus amigos.
          </p>
          <div className="auth-left__features">
            <div className="auth-feature">
              <span className="auth-feature__icon">🏆</span>
              <div className="auth-feature__text">
                <strong>Ligas Privadas</strong>
                Compite contra amigos en tu propia liga
              </div>
            </div>
            <div className="auth-feature">
              <span className="auth-feature__icon">💰</span>
              <div className="auth-feature__text">
                <strong>Mercado en Vivo</strong>
                Subasta y ficha jugadores en tiempo real
              </div>
            </div>
            <div className="auth-feature">
              <span className="auth-feature__icon">⭐</span>
              <div className="auth-feature__text">
                <strong>Jugadores Icono</strong>
                Consigue leyendas del fútbol mundial
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ─── RIGHT — Form Panel ─── */}
      <div className="auth-right">
        <div className="auth-right__orb auth-right__orb--1" />
        <div className="auth-right__orb auth-right__orb--2" />

        <div className="auth-container">
          {/* Mobile brand */}
          <div className="auth-mobile-brand">
            <span className="auth-mobile-brand__icon">
              <img src="/logo-premium.png" alt="UFL" />
            </span>
            <div className="auth-mobile-brand__title">Ultimate Fantasy Legends</div>
            <div className="auth-mobile-brand__sub">Scottish Premiership Fantasy</div>
          </div>

          <div className="auth-card">
            <h2 className="auth-card-title">Bienvenido de nuevo</h2>
            <p className="auth-card-subtitle">Inicia sesión para continuar gestionando tu equipo</p>

            {error && (
              <div className="auth-error">
                <span className="auth-error-icon">⚠️</span>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="auth-field">
                <label htmlFor="email">Email</label>
                <div className="auth-input-wrapper">
                  <span className="auth-input-icon">✉️</span>
                  <input
                    id="email"
                    type="email"
                    placeholder="tu@email.com"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    required
                    autoComplete="email"
                  />
                </div>
              </div>

              <div className="auth-field">
                <label htmlFor="password">Contraseña</label>
                <div className="auth-input-wrapper">
                  <span className="auth-input-icon">🔒</span>
                  <input
                    id="password"
                    type={showPass ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                    minLength={6}
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    className="auth-eye-btn"
                    onClick={() => setShowPass(v => !v)}
                    tabIndex={-1}
                  >
                    {showPass ? '🙈' : '👁️'}
                  </button>
                </div>
              </div>

              <button type="submit" className="auth-submit-btn" disabled={loading}>
                {loading ? (
                  <span className="auth-btn-loading">
                    <span className="auth-spinner" />
                    Entrando...
                  </span>
                ) : (
                  <>
                    <img src="/logo-premium.png" alt="" style={{ width: '24px', height: '24px' }} />
                    Entrar al Juego
                  </>
                )}
              </button>
            </form>

            <div className="auth-divider"><span>¿nuevo aquí?</span></div>

            <p className="auth-switch">
              ¿No tienes cuenta?{' '}
              <Link to="/register" className="auth-switch-link">
                Regístrate gratis →
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
