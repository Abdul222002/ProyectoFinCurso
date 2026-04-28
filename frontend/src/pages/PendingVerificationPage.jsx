import { useSearchParams, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { authAPI } from '../services/endpoints';
import { useState } from 'react';
import './AuthPages.css';

export default function PendingVerificationPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const email = searchParams.get('email');
  const [isSending, setIsSending] = useState(false);
  const [sent, setSent] = useState(false);

  const handleResend = async () => {
    if (!email) {
      toast.error('No se ha proporcionado un email válido');
      return;
    }
    setIsSending(true);
    try {
      await authAPI.resendVerification(email);
      setSent(true);
      toast.success('Te hemos enviado un nuevo correo de verificación');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al enviar el correo. Inténtalo más tarde.');
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="auth-page">
      {/* Panel izquierdo de marca — igual que login/register */}
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
            Un último paso antes de entrar al campo.
          </p>
        </div>
      </div>

      {/* Panel derecho */}
      <div className="auth-right">
        <div className="auth-card">
          <div style={{ textAlign: 'center', marginBottom: '28px' }}>
            <div style={{ fontSize: '56px', marginBottom: '16px', lineHeight: 1 }}>✉️</div>
            <h2 className="auth-card__title" style={{ color: 'var(--text-primary)' }}>
              Revisa tu bandeja de entrada
            </h2>
            <p className="auth-card__subtitle">
              Hemos enviado un enlace de verificación a{' '}
              {email && <strong style={{ color: 'var(--gold)' }}>{email}</strong>}.
              Pulsa en el enlace para activar tu cuenta y empezar a jugar.
            </p>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginTop: '8px' }}>
              ¿No lo encuentras? Revisa la carpeta de <strong>Spam</strong> o Correo no deseado.
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <button
              className="auth-btn"
              onClick={() => navigate('/login')}
            >
              Ir al Login
            </button>
            <button
              className="auth-btn-secondary"
              onClick={handleResend}
              disabled={isSending || sent}
              style={{ opacity: (isSending || sent) ? 0.6 : 1 }}
            >
              {sent ? '✅ Email reenviado' : isSending ? 'Enviando...' : 'Reenviar email de verificación'}
            </button>
          </div>

          <p style={{ textAlign: 'center', marginTop: '20px', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
            ¿Equivocaste el email?{' '}
            <button
              onClick={() => navigate('/register')}
              style={{ background: 'none', border: 'none', color: 'var(--gold)', cursor: 'pointer', fontWeight: 600, fontSize: '0.82rem' }}
            >
              Crear cuenta nueva
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
