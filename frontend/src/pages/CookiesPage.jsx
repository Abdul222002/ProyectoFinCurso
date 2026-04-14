import React from 'react';
import AppLayout from '../components/AppLayout';

export default function CookiesPage() {
  return (
    <AppLayout title="Política de Cookies">
      <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto', color: 'var(--text-primary)' }}>
        
        <h1 style={{ color: 'var(--gold)', marginBottom: '20px' }}>Política de Cookies</h1>
        
        <section style={{ marginBottom: '32px' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '12px', color: 'var(--text-secondary)' }}>1. ¿Qué son las cookies?</h2>
          <p style={{ lineHeight: '1.6', marginBottom: '12px' }}>
            Las cookies son pequeños archivos de texto que se almacenan en su dispositivo (ordenador, tablet, smartphone) cuando visita nuestra aplicación. Sirven para recordar sus preferencias, mantener su sesión activa y garantizar el correcto funcionamiento técnico de la plataforma.
          </p>
        </section>

        <section style={{ marginBottom: '32px' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '12px', color: 'var(--text-secondary)' }}>2. ¿Qué cookies usamos?</h2>
          <p style={{ lineHeight: '1.6', marginBottom: '16px' }}>
            Nuestra aplicación está diseñada respetando su privacidad. <strong>NO utilizamos cookies de terceros, de publicidad, ni de analítica tracking.</strong> Únicamente utilizamos cookies y tecnologías de almacenamiento local estrictamente necesarias (técnicas) para el funcionamiento del juego.
          </p>
          
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '600px' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--border)' }}>
                  <th style={{ padding: '12px', color: 'var(--gold)' }}>Nombre</th>
                  <th style={{ padding: '12px', color: 'var(--gold)' }}>Finalidad</th>
                  <th style={{ padding: '12px', color: 'var(--gold)' }}>Duración</th>
                  <th style={{ padding: '12px', color: 'var(--gold)' }}>Tipo</th>
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '12px' }}><code>token</code> / <code>jwt</code></td>
                  <td style={{ padding: '12px' }}>Mantener la sesión de usuario autenticada para acceder al juego.</td>
                  <td style={{ padding: '12px' }}>Sesión / 7 días</td>
                  <td style={{ padding: '12px' }}>Técnica (Necesaria)</td>
                </tr>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '12px' }}><code>cookie_consent</code></td>
                  <td style={{ padding: '12px' }}>Recordar si el usuario ha interactuado con el banner de cookies para no volver a mostrarlo.</td>
                  <td style={{ padding: '12px' }}>1 año</td>
                  <td style={{ padding: '12px' }}>Técnica (Necesaria)</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '12px' }}>
            * Nota: Al ser cookies y tecnologías de almacenamiento estrictamente necesarias para el uso explícito del servicio (entrar a tu cuenta de juego), la normativa permite su instalación sin requerir un consentimiento expreso bloqueante previo, aunque informamos de ello por transparencia.
          </p>
        </section>

        <section style={{ marginBottom: '32px' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '12px', color: 'var(--text-secondary)' }}>3. Sus Derechos y Control</h2>
          <p style={{ lineHeight: '1.6', marginBottom: '12px' }}>
            Usted puede bloquear o eliminar estas cookies a través de la configuración de su navegador en cualquier momento. Sin embargo, tenga en cuenta que si desactiva las cookies técnicas de sesión, <strong>no podrá iniciar sesión ni jugar</strong>, ya que el sistema no podrá identificar su identidad.
          </p>
        </section>

        <section style={{ marginBottom: '32px' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '12px', color: 'var(--text-secondary)' }}>4. Contacto</h2>
          <p style={{ lineHeight: '1.6' }}>
            Si tiene alguna pregunta sobre el uso de cookies en nuestra plataforma, puede contactarnos a través del siguiente correo electrónico que haya sido configurado para soporte: <strong>[CORREO CONFIGURABLE DEL PROYECTO]</strong>
          </p>
        </section>

      </div>
    </AppLayout>
  );
}
