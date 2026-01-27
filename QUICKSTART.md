# 🚀 Guía de Inicio Rápido

## 📋 Pasos para Iniciar el Proyecto

### 1️⃣ Instalar Dependencias

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# Instalar todas las dependencias
pip install -r requirements.txt
```

### 2️⃣ Configurar Base de Datos MySQL

```sql
-- Abrir MySQL y crear la base de datos
CREATE DATABASE ultimate_fantasy_legends;

-- Verificar que se creó
SHOW DATABASES;
```

### 3️⃣ Configurar Variables de Entorno

Edita el archivo `.env` con tus credenciales:

```env
MYSQL_USER=root
MYSQL_PASSWORD=tu_password_aqui  # ⚠️ IMPORTANTE: Pon tu contraseña de MySQL
MYSQL_DATABASE=ultimate_fantasy_legends
```

### 4️⃣ Poblar la Base de Datos

```bash
# Ejecutar el script de seed (crea tablas y datos de ejemplo)
cd backend
python scripts/seed_db.py
```

Deberías ver:
```
✅ Conexión a MySQL exitosa
📋 Creando tablas...
✅ Base de datos inicializada correctamente
📦 Creando jugadores de ejemplo...
✅ 6 jugadores creados correctamente
🏟️ Creando equipo de ejemplo...
✅ Equipo 'FC Ultimate Legends' creado (OVR: 77.2)
```

### 5️⃣ Iniciar el Servidor

```bash
# Desde el directorio raíz del proyecto
cd backend
uvicorn app.main:app --reload
```

Deberías ver:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### 6️⃣ Probar la API

Abre tu navegador en:

- **Documentación Swagger**: http://localhost:8000/docs
- **Endpoint raíz**: http://localhost:8000/
- **Health check**: http://localhost:8000/health

---

## 📁 Estructura Creada

```
ProyectoFinCurso/
├── .env                          ✅ Configuración
├── .gitignore                    ✅ Archivos a ignorar
├── requirements.txt              ✅ Dependencias
├── README.md                     ✅ Documentación
│
├── backend/
│   ├── app/
│   │   ├── __init__.py          ✅
│   │   ├── main.py              ✅ FastAPI app
│   │   ├── core/
│   │   │   ├── __init__.py      ✅
│   │   │   ├── config.py        ✅ Lee .env
│   │   │   └── database.py      ✅ Conexión MySQL
│   │   ├── models/
│   │   │   ├── __init__.py      ✅
│   │   │   ├── player.py        ✅ Modelo Jugador
│   │   │   └── team.py          ✅ Modelo Equipo
│   │   ├── schemas/
│   │   │   └── __init__.py      ✅
│   │   ├── routers/
│   │   │   └── __init__.py      ✅
│   │   └── services/
│   │       └── __init__.py      ✅
│   └── scripts/
│       └── seed_db.py           ✅ Poblar BD
│
└── frontend/
    └── .gitkeep                  ✅ (pendiente)
```

---

## 🎯 Próximos Pasos

1. ✅ **Scaffolding completo**
2. ⏳ **Instalar dependencias y probar el servidor**
3. 📝 Crear routers para la API
4. 🔐 Implementar autenticación JWT
5. 🌐 Integrar Sportmonks API
6. ⚛️ Crear frontend con React + Vite

---

## 🐛 Solución de Problemas

### Error: "No module named 'app'"
```bash
# Asegúrate de estar en el directorio backend
cd backend
python scripts/seed_db.py
```

### Error: "Access denied for user"
```bash
# Verifica tu contraseña en .env
MYSQL_PASSWORD=tu_password_correcta
```

### Error: "Unknown database"
```sql
-- Crea la base de datos primero
CREATE DATABASE ultimate_fantasy_legends;
```

---

¡Todo listo para empezar a desarrollar! 🚀⚽
