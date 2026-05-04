import os
import secrets
from datetime import datetime, timedelta
import logging
import threading

from app.core.config import settings

logger = logging.getLogger(__name__)

SMTP_HOST = settings.SMTP_HOST
SMTP_PORT = settings.SMTP_PORT
SMTP_USER = settings.SMTP_USER
SMTP_PASSWORD = settings.SMTP_PASSWORD
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")

def generate_verification_token() -> tuple[str, datetime]:
    """Genera un código OTP de 6 dígitos y su expiración (15 min)"""
    code = f"{secrets.randbelow(1000000):06d}"
    expires = datetime.utcnow() + timedelta(minutes=15)
    return code, expires


def _build_html(username: str, code: str) -> str:
    return f"""
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


def _send_via_resend(to_email: str, username: str, code: str):
    """Envía email via Resend API (HTTPS, no se bloquea en Railway)"""
    import requests

    subject = "Verifica tu cuenta en Scottish Premier Legends"
    html = _build_html(username, code)

    logger.info(f"📧 [Resend] Enviando a {to_email}")

    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": "SPL Game <onboarding@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "html": html,
        },
        timeout=10,
    )

    if resp.status_code == 200:
        logger.info(f"✅ [Resend] Email enviado a {to_email}: {resp.json().get('id')}")
    else:
        logger.error(f"❌ [Resend] Error {resp.status_code}: {resp.text}")
        raise Exception(f"Resend error {resp.status_code}: {resp.text}")


def _send_via_smtp(to_email: str, username: str, code: str):
    """Envía email via SMTP (fallback si no hay Resend)"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import ssl

    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("⚠️ SMTP credentials not set.")
        return

    subject = "Verifica tu cuenta en Scottish Premier Legends"
    html = _build_html(username, code)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"SPL Game <{SMTP_USER}>"
    msg['To'] = to_email
    msg.attach(MIMEText(html, 'html'))

    context = ssl.create_default_context()

    logger.info(f"📧 [SMTP] Enviando a {to_email} via {SMTP_HOST}:{SMTP_PORT}")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
            logger.info(f"✅ [SMTP] Email enviado a {to_email}")
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"❌ [SMTP] Auth Error: {e}")
        raise
    except smtplib.SMTPConnectError as e:
        logger.error(f"❌ [SMTP] Connect Error: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ [SMTP] Error: {e}")
        raise


def send_verification_email(to_email: str, username: str, code: str):
    """Envía el email de verificación.
    
    Prioridad: Resend API > SMTP (background thread)
    """
    if RESEND_API_KEY:
        # Resend usa HTTPS, Railway no lo bloquea
        _send_via_resend(to_email, username, code)
    else:
        # SMTP en thread para no bloquear la respuesta del registro
        logger.info("⚠️ No hay RESEND_API_KEY, usando SMTP como fallback")
        t = threading.Thread(
            target=_send_via_smtp,
            args=(to_email, username, code),
            daemon=True,
        )
        t.start()
