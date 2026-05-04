import os
import secrets
from datetime import datetime, timedelta
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


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
    """Envía email via Resend API"""
    import requests

    resend_key = os.environ.get("RESEND_API_KEY", "").strip()
    logger.info(f"📧 [Resend] API key presente: {bool(resend_key)}, inicio: {resend_key[:6]}...")

    subject = "Verifica tu cuenta en Scottish Premier Legends"
    html = _build_html(username, code)

    logger.info(f"📧 [Resend] Enviando a {to_email}")

    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {resend_key}",
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
        data = resp.json()
        logger.info(f"✅ [Resend] Email enviado a {to_email}, ID: {data.get('id')}")
    else:
        logger.error(f"❌ [Resend] Error {resp.status_code}: {resp.text}")
        raise Exception(f"Resend error {resp.status_code}: {resp.text}")


def send_verification_email(to_email: str, username: str, code: str):
    """Envía el email de verificación usando Resend API en thread separado."""
    import threading
    
    resend_key = os.environ.get("RESEND_API_KEY", "").strip()
    logger.info(f"📧 Email a {to_email} — RESEND_API_KEY configurada: {bool(resend_key)}")
    
    if not resend_key:
        logger.error("⚠️ RESEND_API_KEY no está configurada. Email NO enviado.")
        return
    
    def _send_in_background():
        try:
            _send_via_resend(to_email, username, code)
        except Exception as e:
            logger.error(f"❌ Error enviando email a {to_email}: {e}")
    
    t = threading.Thread(target=_send_in_background, daemon=True)
    t.start()
    logger.info(f"📧 Thread de envío iniciado para {to_email}")
