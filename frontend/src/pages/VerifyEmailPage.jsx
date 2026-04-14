import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import AppLayout from '../components/AppLayout';
import { toast } from 'sonner';
import { authAPI } from '../services/endpoints';

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');
  
  const [status, setStatus] = useState('loading'); // loading, success, error
  const [email] = useState(searchParams.get('email') || '');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      return;
    }

    const verify = async () => {
      try {
        await authAPI.verifyEmail(token);
        setStatus('success');
      } catch (err) {
        setStatus('error');
      }
    };
    
    verify();
  }, [token]);

  const handleResend = async () => {
    if (!email) {
      toast.error('No se encontró el email para reenviar');
      return;
    }
    
    try {
      await authAPI.resendVerification(email);
      toast.success('Email de verificación reenviado a tu bandeja');
    } catch (err) {
      toast.error('Error al reenviar el email. Inténtalo de nuevo más tarde.');
    }
  };

  return (
    <AppLayout title="Verificación de Email" hideSidebar>
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
          
          {status === 'loading' && (
            <>
              <h2 style={{ color: 'var(--text-primary)', marginBottom: '16px' }}>Verificando...</h2>
              <p style={{ color: 'var(--text-secondary)' }}>Por favor, espera mientras procesamos tu solicitud de verificación.</p>
            </>
          )}

          {status === 'success' && (
            <>
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>✅</div>
              <h2 style={{ color: 'var(--gold)', marginBottom: '16px' }}>¡Email Verificado!</h2>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '32px' }}>
                Tu cuenta ha sido activada correctamente. Ya puedes acceder al juego.
              </p>
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
            </>
          )}

          {status === 'error' && (
            <>
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>⚠️</div>
              <h2 style={{ color: 'var(--danger, #ff4c4c)', marginBottom: '16px' }}>Enlace Inválido o Expirado</h2>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '32px' }}>
                El enlace de verificación no es válido o ha caducado (suelen durar 24 horas).
              </p>
              {email ? (
                <button 
                  onClick={handleResend}
                  style={{
                    background: 'transparent',
                    color: 'var(--gold)',
                    border: '1px solid var(--gold)',
                    padding: '12px 24px',
                    borderRadius: '8px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    width: '100%',
                    marginBottom: '16px'
                  }}
                >
                  Volver a Enviar Email
                </button>
              ) : (
                <button 
                  onClick={() => navigate('/login')}
                  style={{
                    background: 'var(--bg-hover)',
                    color: 'var(--text-primary)',
                    border: 'none',
                    padding: '12px 24px',
                    borderRadius: '8px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    width: '100%'
                  }}
                >
                  Volver a Iniciar Sesión
                </button>
              )}
            </>
          )}

        </div>
      </div>
    </AppLayout>
  );
}
