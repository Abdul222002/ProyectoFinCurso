import { useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authAPI } from '../services/endpoints';
import { toast } from 'sonner';
import './AuthPages.css';

export default function VerifyEmailPage() {
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [searchParams] = useSearchParams();
  const emailParam = searchParams.get('email') || '';
  const navigate = useNavigate();

  const handleResend = async () => {
    if (!emailParam) {
      toast.error('No se ha proporcionado un email válido');
      return;
    }
    setIsSending(true);
    try {
      await authAPI.resendVerification(emailParam);
      setSent(true);
      toast.success('Te hemos enviado un nuevo código de verificación');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al enviar el correo. Inténtalo más tarde.');
    } finally {
      setIsSending(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (code.length !== 6) {
      setError('El código debe tener 6 dígitos.');
      return;
    }

    if (!emailParam) {
      setError('No se ha proporcionado un correo electrónico. Vuelve a iniciar sesión.');
      return;
    }

    setLoading(true);
    try {
      // Usar la nueva API de authAPI para enviar email y code
      const response = await authAPI.verifyEmailOtp({ email: emailParam, code });
      
      const { access_token } = response.data;
      
      // Auto login after verification
      localStorage.setItem('token', access_token);
      window.location.href = '/dashboard';
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Código incorrecto o caducado. Inténtalo de nuevo.');
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
          <h1 className="auth-left__title">Seguridad<br /><span>Total</span></h1>
          <p className="auth-left__desc">
            Protegemos tu equipo y tus progresos. Solo tú puedes acceder a tu plantilla de estrellas.
          </p>
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
          </div>

          <div className="auth-card">
            <h2 className="auth-card-title">Verifica tu Email</h2>
            <p className="auth-card-subtitle">
              Hemos enviado un código de 6 dígitos a:<br/>
              <strong>{emailParam || 'tu correo'}</strong>
            </p>

            {error && (
              <div className="auth-error">
                <span className="auth-error-icon">⚠️</span>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="auth-field">
                <label htmlFor="code">Código de Verificación</label>
                <div className="auth-input-wrapper">
                  <span className="auth-input-icon">🔐</span>
                  <input
                    id="code"
                    type="text"
                    placeholder="Ej: 123456"
                    value={code}
                    onChange={e => setCode(e.target.value.replace(/[^0-9]/g, '').slice(0, 6))}
                    required
                    maxLength={6}
                    style={{ letterSpacing: '8px', fontSize: '1.2rem', textAlign: 'center' }}
                  />
                </div>
              </div>

              <button type="submit" className="auth-submit-btn" disabled={loading || code.length !== 6}>
                {loading ? (
                  <span className="auth-btn-loading">
                    <span className="auth-spinner" />
                    Comprobando...
                  </span>
                ) : (
                  <>Verificar y Entrar</>
                )}
              </button>
            </form>

            <div className="auth-divider"><span>¿no has recibido el código?</span></div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <button
                className="auth-btn-secondary"
                onClick={handleResend}
                disabled={isSending || sent}
                style={{ opacity: (isSending || sent) ? 0.6 : 1 }}
                type="button"
              >
                {sent ? '✅ Código reenviado' : isSending ? 'Enviando...' : 'Reenviar código de verificación'}
              </button>
            </div>

            <p className="auth-switch" style={{ marginTop: '20px' }}>
              ¿Equivocaste el email?{' '}
              <Link to="/register" className="auth-switch-link">
                Crear cuenta nueva
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
