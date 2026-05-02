"""
Router de Autenticación - Login, Register, Me
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from fastapi.security import OAuth2PasswordBearer
from typing import List

from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.config import settings
from app.models.models import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse, VerifyEmailRequest, UserProfileUpdate
from app.services.email_service import generate_verification_token, send_verification_email

router = APIRouter()

# ==========================================
# CONFIGURACIÓN DE SEGURIDAD
# ==========================================

# Hash de contraseñas con bcrypt (native)
# OAuth2 scheme para extraer el token del header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que la contraseña coincida con el hash"""
    try:
        truncated = plain_password.encode('utf-8')[:72]
        return bcrypt.checkpw(truncated, hashed_password.encode('utf-8'))
    except Exception:
        return False


def hash_password(password: str) -> str:
    """Genera hash bcrypt de la contraseña"""
    truncated = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(truncated, salt).decode('utf-8')


def create_access_token(data: dict) -> str:
    """Crea un JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Dependency: obtiene el usuario actual desde el JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: sin identificador de usuario",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = int(user_id_str)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido o expirado: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Validar verificación de email (bloqueo global)
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email no verificado. Revisa tu bandeja de entrada."
        )
        
    return user


# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo usuario y devuelve token JWT
    """
    # Verificar si el email ya existe
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este email ya está registrado"
        )

    # Verificar si el username ya existe
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este nombre de usuario ya está en uso"
        )

    # Crear usuario y código OTP
    token, expires = generate_verification_token()
    
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        verification_token=token,
        verification_token_expires=expires,
        email_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Enviar email
    try:
        send_verification_email(new_user.email, new_user.username, token)
    except Exception as e:
        print(f"ERROR: No se pudo enviar el email de verificación a {new_user.email}: {e}")

    # Generar token — sub DEBE ser string
    access_token = create_access_token(data={"sub": str(new_user.id)})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(new_user)
    )

@router.post("/verify-email", response_model=TokenResponse)
async def verify_email_otp(data: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verifica el código OTP enviado por email"""
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    if user.email_verified:
        raise HTTPException(status_code=400, detail="El email ya está verificado")
        
    if user.verification_token != data.code:
        raise HTTPException(status_code=400, detail="Código de verificación incorrecto")
        
    import datetime
    if user.verification_token_expires and datetime.datetime.utcnow() > user.verification_token_expires:
        raise HTTPException(status_code=400, detail="El código de verificación ha caducado")
        
    # Verificar usuario
    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()
    
    # Generar token de acceso para login automático tras verificar
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )
@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Login de usuario - devuelve token JWT
    """
    # Buscar usuario por email
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )

    # Verificar contraseña
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )
        
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Debes verificar tu email antes de iniciar sesión. Revisa tu bandeja de entrada."
        )

    # Actualizar last_login
    user.last_login = datetime.utcnow()
    db.commit()

    # Generar token — sub DEBE ser string
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.verification_token == token,
        User.verification_token_expires > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")
    
    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()
    
    return {"message": "Email verificado correctamente"}

@router.post("/resend-verification")
async def resend_verification(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or user.email_verified:
        return {"message": "Si el email existe y no está verificado, recibirás un nuevo enlace"}
    
    token, expires = generate_verification_token()
    user.verification_token = token
    user.verification_token_expires = expires
    db.commit()
    
    try:
        send_verification_email(user.email, user.username, token)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al enviar el email")
    
    return {"message": "Email de verificación reenviado"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Devuelve los datos del usuario autenticado
    """
    return UserResponse.model_validate(current_user)



@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza el perfil del usuario (nombre de usuario)
    """
    # Verificar si el username ya está en uso por otro usuario
    existing_user = db.query(User).filter(
        User.username == profile_data.username,
        User.id != current_user.id
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está en uso"
        )
        
    current_user.username = profile_data.username
    if profile_data.avatar_url is not None:
        current_user.avatar_url = profile_data.avatar_url
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)

@router.get("/search", response_model=List[UserResponse])
async def search_users(
    q: str,
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Busca usuarios por nombre de usuario o email
    """
    if not q or len(q) < 2:
        return []
        
    users = db.query(User).filter(
        or_(
            User.username.ilike(f"%{q}%"),
            User.email.ilike(f"%{q}%")
        )
    ).limit(limit).all()
    
    return [UserResponse.model_validate(u) for u in users]
