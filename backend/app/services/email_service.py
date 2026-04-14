import resend
import os
import secrets
from datetime import datetime, timedelta

resend.api_key = os.getenv("RESEND_API_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

def generate_verification_token() -> tuple[str, datetime]:
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=24)
    return token, expires

def send_verification_email(to_email: str, username: str, token: str):
    verify_url = f"{FRONTEND_URL}/verify-email?token={token}"
    
    html = f"""
    <div style="font-family: Inter, sans-serif; max-width: 600px; margin: 0 auto; background: #080d1a; color: #f0f4ff; padding: 40px; border-radius: 16px;">
        <div style="text-align: center; margin-bottom: 32px;">
            <h1 style="color: #c9a84c; font-size: 2rem; margin: 0;">⚽ Scottish Premier Legends</h1>
        </div>
        <h2 style="color: #f0f4ff;">Verifica tu cuenta, {username}</h2>
        <p style="color: #8a9bc4; line-height: 1.6;">
            Gracias por registrarte. Haz clic en el botón de abajo para verificar tu email y activar tu cuenta.
        </p>
        <div style="text-align: center; margin: 32px 0;">
            <a href="{verify_url}" 
               style="background: linear-gradient(135deg, #c9a84c, #9a7a2e); color: #080d1a; 
                      padding: 16px 32px; border-radius: 10px; font-weight: 800; 
                      text-decoration: none; display: inline-block; font-size: 1rem;">
                ✅ Verificar Email
            </a>
        </div>
        <p style="color: #4a5a7a; font-size: 0.85rem; text-align: center;">
            Este enlace caduca en 24 horas. Si no te has registrado, ignora este email.
        </p>
    </div>
    """
    
    resend.Emails.send({
        "from": "SPL Game <noreply@resend.dev>",  
        "to": [to_email],
        "subject": "Verifica tu cuenta en Scottish Premier Legends",
        "html": html
    })
