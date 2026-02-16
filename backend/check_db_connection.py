import sys
import os

sys.path.append(os.getcwd())

print("--- Verificando entorno completo ---")

errors = []

# 1. Dependencias de Auth
try:
    from jose import jwt
    print("✅ python-jose instalado")
except ImportError:
    print("❌ python-jose NO instalado")
    errors.append("python-jose")

try:
    from passlib.context import CryptContext
    print("✅ passlib instalado")
except ImportError:
    print("❌ passlib NO instalado")
    errors.append("passlib")

try:
    from email_validator import validate_email, EmailNotValidError
    print("✅ email-validator instalado")
except ImportError:
    print("❌ email-validator NO instalado (Necesario para Pydantic EmailStr)")
    errors.append("email-validator")

print("\n--- Verificando Hash Hasher ---")
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hash_test = pwd_context.hash("test")
    print("✅ Password hashing (bcrypt) funcional")
except Exception as e:
    print(f"❌ Error en hashing password: {e}")
    errors.append(f"Fallo hashing: {e}")

# 2. Base de datos y Tablas
try:
    from sqlalchemy import create_engine, inspect
    from app.core.config import settings
    
    print(f"Conectando a DB...")
    engine = create_engine(settings.database_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"✅ Conexión exitosa. Tablas encontradas: {', '.join(tables)}")
    
    if "users" in tables:
        print("✅ Tabla 'users' EXISTE")
    else:
        print("❌ Tabla 'users' NO EXISTE (Esto causará error 500 en login/register)")
        errors.append("Tabla users faltante")
        
except Exception as e:
    print(f"❌ Error DB: {e}")
    errors.append(str(e))

if errors:
    print("\nPROBLEMAS ENCONTRADOS:")
    for err in errors:
        print(f"- {err}")
    sys.exit(1)
else:
    print("\nTodo parece correcto. Si sigue fallando, revisa los logs de la terminal de uvicorn (backend).")
