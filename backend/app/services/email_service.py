import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import secrets
from datetime import datetime, timedelta
import ssl
import threading
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

SMTP_HOST = settings.SMTP_HOST
SMTP_PORT = settings.SMTP_PORT
SMTP_USER = settings.SMTP_USER
SMTP_PASSWORD = settings.SMTP_PASSWORD

def generate_verification_token() -> tuple[str, datetime]:
    """Generates a 6-digit OTP code and its expiration time (15 mins)"""
    code = f"{secrets.randbelow(1000000):06d}"
    expires = datetime.utcnow() + timedelta(minutes=15)
    return code, expires

def _send_smtp_email_sync(to_email: str, username: str, code: str):
    """Envía email via SMTP con timeout. Función síncrona con timeout."""
    logger.info(f"📧 Iniciando envío SMTP a {to_email}")
    logger.info(f"📧 Host: {SMTP_HOST}, Port: {SMTP_PORT}, User: {SMTP_USER}")

    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("⚠️ SMTP credentials not set. Email not sent.")
        return

    subject = "Verifica tu cuenta en Scottish Premier Legends"
    
    html = f"""
    <div style="font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #ffffff; color: #1e293b; padding: 40px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
        <div style="text-align: center; margin-bottom: 32px; border-bottom: 2px solid #e2e8f0; padding-bottom: 20px;">
            <h1 style="color: #1d4ed8; font-size: 24px; margin: 0; font-weight: 800; letter-spacing: 0.5px;">⚽ Scottish Premier Legends</h1>
        </div>
        <h2 style="color: #0f172a; font-size: 20px; font-weight: 700; margin-bottom: 16px;">Hola, {username}.</h2>
        <p style="color: #475569; line-height: 1.6; font-size: 16px; margin-bottom: 32px;">
            Para completar tu registro y acceder a la plataforma, utiliza el siguiente código de verificación:
        </p>
        
        <div style="text-align: center; margin: 32px 0; background: #f8fafc; padding: 24px; border-radius: 8px; border: 1px dashed #cbd5e1;">
            <div style="font-size: 36px; font-weight: 900; letter-spacing: 8px; color: #1d4ed8;">
                {code}
            </div>
        </div>
        
        <p style="color: #64748b; font-size: 14px; text-align: center; margin-top: 32px;">
            Este código expirará en 15 minutos.
        </p>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center;">
            <p style="color: #94a3b8; font-size: 12px; margin: 0;">
                © 2026 Scottish Premier Legends. Todos los derechos reservados.
            </p>
        </div>
    </div>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"SPL Game <{SMTP_USER}>"
    msg['To'] = to_email

    msg.attach(MIMEText(html, 'html'))

    context = ssl.create_default_context()
    
    try:
        logger.info(f"📧 Conectando a {SMTP_HOST}:{SMTP_PORT}...")
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.set_debuglevel(1)
            logger.info("📧 Enviando EHLO...")
            server.ehlo()
            logger.info("📧 Iniciando STARTTLS...")
            server.starttls(context=context)
            server.ehlo()
            logger.info("📧 Haciendo login...")
            server.login(SMTP_USER, SMTP_PASSWORD)
            logger.info("📧 Enviando mensaje...")
            server.send_message(msg)
            logger.info(f"✅ Email de verificación enviado a {to_email}")
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"❌ SMTP Authentication Error: {e}. Revisa SMTP_USER y SMTP_PASSWORD en Railway")
        raise
    except smtplib.SMTPConnectError as e:
        logger.error(f"❌ SMTP Connect Error: {e}. Railway podría estar bloqueando el puerto {SMTP_PORT}")
        raise
    except smtplib.SMTPException as e:
        logger.error(f"❌ SMTP Error: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Error desconocido enviando email: {e}")
        raise

def send_verification_email(to_email: str, username: str, code: str):
    """Envía email via SMTP en thread separado para no bloquear la respuesta."""
    logger.info(f"📧 Preparando envío de verificación a {to_email}")
    t = threading.Thread(target=_send_smtp_email_sync, args=(to_email, username, code), daemon=True)
    t.start()
    logger.info(f"📧 Thread de envío iniciado para {to_email}")

