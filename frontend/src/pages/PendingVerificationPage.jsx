import { useSearchParams, useNavigate } from 'react-router-dom';
import AppLayout from '../components/AppLayout';
import { toast } from 'sonner';
import { authAPI } from '../services/endpoints';
import { useState } from 'react';

export default function PendingVerificationPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const email = searchParams.get('email');
  const [isSending, setIsSending] = useState(false);

  const handleResend = async () => {
    if (!email) {
      toast.error('No se ha proporcionado un email válido');
      return;
    }

    setIsSending(true);
    try {
      await authAPI.resendVerification(email);
      toast.success('Te hemos enviado un nuevo correo de verificación');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al enviar el correo');
    } finally {
      setIsSending(false);
    }
  };

  return (
    <AppLayout title="Verifica tu Email" hideSidebar>
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <div style={{ 
          background: 'var(--bg-elevated)', 
          padding: '40px', 
          borderRadius: '16px', 
          border: '1px solid var(--border)',
          maxWidth: '500px',
          width: '100%',
          textAlign: 'center'
        }}>
          
          <div style={{ fontSize: '48px', marginBottom: '20px' }}>✉️</div>
          <h2 style={{ color: 'var(--text-primary)', marginBottom: '16px' }}>
            Revisa tu bandeja de entrada
          </h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '12px', lineHeight: '1.6' }}>
            Hemos enviado un enlace de verificación a <strong>{email}</strong>. 
            Por favor, pulsa en él para activar tu cuenta y empezar a jugar.
          </p>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '32px' }}>
            Si no lo encuentras, revisa tu carpeta de Spam o Correo no deseado.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <button 
              onClick={() => navigate('/login')}
              style={{
                background: 'var(--gold)',
                color: '#000',
                padding: '12px 24px',
                borderRadius: '8px',
                fontWeight: '700',
                border: 'none',
                cursor: 'pointer',
                width: '100%'
              }}
            >
              Ir al Login
            </button>
            <button 
              onClick={handleResend}
              disabled={isSending}
              style={{
                background: 'transparent',
                color: 'var(--text-secondary)',
                border: '1px solid var(--border)',
                padding: '12px 24px',
                borderRadius: '8px',
                fontWeight: '600',
                cursor: isSending ? 'not-allowed' : 'pointer',
                width: '100%',
                opacity: isSending ? 0.7 : 1
              }}
            >
              {isSending ? 'Enviando...' : 'Reenviar email de verificación'}
            </button>
          </div>

        </div>
      </div>
    </AppLayout>
  );
}
