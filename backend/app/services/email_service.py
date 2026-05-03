import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import secrets
from datetime import datetime, timedelta
import ssl

from app.core.config import settings

SMTP_HOST = settings.SMTP_HOST
SMTP_PORT = settings.SMTP_PORT
SMTP_USER = settings.SMTP_USER
SMTP_PASSWORD = settings.SMTP_PASSWORD

def generate_verification_token() -> tuple[str, datetime]:
    """Generates a 6-digit OTP code and its expiration time (15 mins)"""
    # Generate 6-digit string
    code = f"{secrets.randbelow(1000000):06d}"
    expires = datetime.utcnow() + timedelta(minutes=15)
    return code, expires

def send_verification_email(to_email: str, username: str, code: str):
    """Sends the OTP code via SMTP with the White and Blue theme."""
    if not SMTP_USER or not SMTP_PASSWORD:
        print("WARNING: SMTP credentials not set. Email not sent.")
        return

    subject = "Verifica tu cuenta en Scottish Premier Legends"
    
    # White and Blue theme, similar to standard corporate emails
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
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise e
