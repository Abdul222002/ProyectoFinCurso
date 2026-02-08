# INSTRUCCIONES PARA EJECUTAR EL TEST DE LA API

## 🎯 Objetivo
Verificar qué estadísticas devuelve la API de Sportmonks y calcular puntos fantasy

## 📋 Requisitos
1. Python 3.10+ instalado
2. Variable de entorno SPORTMONKS_API_KEY configurada en .env
3. Librería `requests` instalada

## 🚀 Cómo ejecutar

### Opción 1: Con virtual environment
```bash
cd c:\Users\abdul22\OneDrive\Escritorio\ProyectoFinCurso

# Crear venv si no existe
python -m venv backend\venv

# Activar
backend\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install requests python-dotenv

# Ejecutar test
python backend\scripts\test_api_stats.py
```

### Opción 2: Python directo (si está en PATH)
```bash
cd c:\Users\abdul22\OneDrive\Escritorio\ProyectoFinCurso
python backend\scripts\test_api_stats.py
```

### Opción 3: Python desde Microsoft Store
Si no tienes Python instalado, descárgalo desde Microsoft Store o python.org

## 📊 Qué hace el script

1. **Obtiene último partido** de la Scottish Premiership 2025/26
2. **Extrae estadísticas** de los primeros 5 jugadores:
   - Minutos jugados
   - Goles
   - Asistencias
   - Tarjetas amarillas/rojas
   - Nota del partido
   - Y otras estadísticas disponibles
3. **Calcula puntos fantasy** usando la fórmula diferenciada por posición:
   - GK gol: +10, DEF gol: +7, MID gol: +5, FWD gol: +4
   - GK asist: +5, DEF asist: +4, MID asist: +3, FWD asist: +2
   - Clean sheets, minutos, notas

## 📝 Output esperado

```
================================================================================
📡 OBTENIENDO ÚLTIMOS PARTIDOS DE LA TEMPORADA
================================================================================

✅ Partido encontrado:
   Celtic vs Rangers
   ID: 12345678
   Fecha: 2026-01-25T15:00:00Z

================================================================================
📊 OBTENIENDO ESTADÍSTICAS DEL PARTIDO 12345678
================================================================================

🏟️  Celtic 2 - 1 Rangers

✅ 22 jugadores encontrados

================================================================================

1. Callum McGregor
   Posición: 30 (MID)
   Titular: Sí

   📊 ESTADÍSTICAS DISPONIBLES:
   ----------------------------------------------------------------------
   Minutes Played                 90
   Goals                          1
   Assists                        1
   Yellow Cards                   0
   Red Cards                      0
   Rating                         8.5
   Passes                         85
   Tackles                        4

   🎯 DATOS PARA PUNTOS FANTASY:
   ----------------------------------------------------------------------
   minutes_played       90
   goals                1
   assists              1
   yellowcards          0
   redcards             0
   rating               8.5

   ⚡ PUNTOS FANTASY CALCULADOS: 13 puntos
   ----------------------------------------------------------------------
   (Cálculo: 1 gol MID +5, 1 asist +3, 90 min +2, nota 8.5 +3 = 13)

... (otros 4 jugadores)

✅ PRUEBA COMPLETADA
```

## ⚠️ Posibles problemas

### Error: No se encontró Python
**Solución:** Instala Python desde https://www.python.org/downloads/ 
o Microsoft Store

### Error: SPORTMONKS_API_KEY no configurada
**Solución:** Asegúrate que el archivo `.env` existe en la raíz del proyecto y contiene:
```
SPORTMONKS_API_KEY=tu_api_key_aqui
```

### Error: Module 'requests' not found
**Solución:**
```bash
pip install requests python-dotenv
```

### Error: 401 Unauthorized
**Solución:** Verifica que tu API key sea correcta y esté activa

## 🎯 Siguiente paso

Después de ejecutar este script sabremos:
- ✅ Qué estadísticas exactas devuelve la API
- ✅ Si faltan datos importantes
- ✅ Si los cálculos de puntos son correctos
- ✅ La estructura exacta de los datos para el sistema definitivo
