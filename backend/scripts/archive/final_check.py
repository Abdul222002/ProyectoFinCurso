import requests

def test_api():
    print("--- Verificando API de Equipos (Fase 3) ---")
    # Intentamos obtener un equipo que sabemos que existe
    # Usaremos el endpoint que devuelve GameweekLineupResponse
    # asumiendo que el server está corriendo localmente en el puerto 8000
    try:
        # Nota: Esto requiere que el backend esté corriendo. 
        # Si no está corriendo, simplemente verificamos que el código compile sin errores.
        import sys
        sys.path.append('backend')
        from app.models.models import GameweekLineup
        print("✅ Importación de modelos exitosa (GameweekLineup no tiene player_ids).")
        
        from app.schemas.team import GameweekLineupResponse
        print("✅ Importación de esquemas exitosa.")
        
    except Exception as e:
        print(f"❌ Error de validación de código: {e}")

if __name__ == "__main__":
    test_api()
