import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './AuthPages.css';

export default function RegisterPage() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden. Comprueba que hayas escrito lo mismo en ambos campos.');
      return;
    }
    if (password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres.');
      return;
    }

    setLoading(true);
    try {
      await register(username, email, password);
      navigate(`/pending-verification?email=${encodeURIComponent(email)}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al crear la cuenta. Inténtalo de nuevo.');
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
          <div className="auth-left__logo-wrap">🏆</div>
          <h1 className="auth-left__title">Únete a la<br /><span>Liga</span></h1>
          <p className="auth-left__desc">
            Crea tu cuenta en segundos y recibe tu plantilla inicial de 15 jugadores de la Scottish Premiership.
          </p>
          <div className="auth-left__features">
            <div className="auth-feature">
              <span className="auth-feature__icon">🃏</span>
              <div className="auth-feature__text">
                <strong>15 Jugadores Iniciales</strong>
                Te asignamos tu plantilla automáticamente
              </div>
            </div>
            <div className="auth-feature">
              <span className="auth-feature__icon">🤝</span>
              <div className="auth-feature__text">
                <strong>Invita a tus Amigos</strong>
                Crea ligas privadas con código de invitación
              </div>
            </div>
            <div className="auth-feature">
              <span className="auth-feature__icon">📊</span>
              <div className="auth-feature__text">
                <strong>Estadísticas Reales</strong>
                Puntos basados en el rendimiento real
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
            <span className="auth-mobile-brand__icon">🏆</span>
            <div className="auth-mobile-brand__title">Ultimate Fantasy Legends</div>
            <div className="auth-mobile-brand__sub">Crea tu cuenta y empieza a jugar</div>
          </div>

          <div className="auth-card">
            <h2 className="auth-card-title">Crear Cuenta</h2>
            <p className="auth-card-subtitle">Es gratis y solo tarda 30 segundos</p>

            {error && (
              <div className="auth-error">
                <span className="auth-error-icon">⚠️</span>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="auth-field">
                <label htmlFor="username">Nombre de Manager</label>
                <div className="auth-input-wrapper">
                  <span className="auth-input-icon">👤</span>
                  <input
                    id="username"
                    type="text"
                    placeholder="Tu apodo de entrenador"
                    value={username}
                    onChange={e => setUsername(e.target.value)}
                    required
                    minLength={3}
                    maxLength={50}
                    autoComplete="username"
                  />
                </div>
              </div>

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
                    placeholder="Mínimo 6 caracteres"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                    minLength={6}
                    autoComplete="new-password"
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

              <div className="auth-field">
                <label htmlFor="confirmPassword">Confirmar Contraseña</label>
                <div className="auth-input-wrapper">
                  <span className="auth-input-icon">🔑</span>
                  <input
                    id="confirmPassword"
                    type={showConfirm ? 'text' : 'password'}
                    placeholder="Repite tu contraseña"
                    value={confirmPassword}
                    onChange={e => setConfirmPassword(e.target.value)}
                    required
                    minLength={6}
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    className="auth-eye-btn"
                    onClick={() => setShowConfirm(v => !v)}
                    tabIndex={-1}
                  >
                    {showConfirm ? '🙈' : '👁️'}
                  </button>
                </div>
              </div>

              <button type="submit" className="auth-submit-btn" disabled={loading}>
                {loading ? (
                  <span className="auth-btn-loading">
                    <span className="auth-spinner" />
                    Creando cuenta...
                  </span>
                ) : '🏆 Crear Cuenta y Jugar'}
              </button>
            </form>

            <p className="auth-terms">
              Al registrarte aceptas nuestras{' '}
              <a href="/cookies" target="_blank" rel="noreferrer">condiciones de uso y política de cookies</a>.
            </p>

            <div className="auth-divider"><span>¿ya tienes cuenta?</span></div>

            <p className="auth-switch">
              <Link to="/login" className="auth-switch-link">
                ← Iniciar Sesión
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
