import requests

API_TOKEN = 'uE2hA7iHbThgr4DjSOXCZEMYK7mIja06CEM4RooUWltOIUjXad9hqU4DqcYp'

CLAVES_ESCOCESAS = [
    "Celtic", "Rangers", "Aberdeen", "Hearts", "Hibernian", 
    "Dundee", "Motherwell", "St. Mirren", "Kilmarnock", 
    "Ross County", "St. Johnstone", "Livingston", "Falkirk"
]

def es_equipo_escoces(nombre_completo):
    for clave in CLAVES_ESCOCESAS:
        if clave in nombre_completo:
            return True
    return False

def obtener_ids_partidos_j3():
    base_url = "https://api.sportmonks.com/v3/football/fixtures/between"
    params = {
        'api_token': API_TOKEN,
        'include': 'participants', # Solo necesitamos los nombres para filtrar
    }

    # Fechas en las que se dividió la jornada
    periodos = [
        ("2025-08-22", "2025-08-25"),
        ("2025-09-22", "2025-09-24")
    ]

    partidos_finales = []

    print(f"📡 Recuperando IDs de partidos para estadísticas...")

    try:
        for inicio, fin in periodos:
            url = f"{base_url}/{inicio}/{fin}"
            response = requests.get(url, params=params)
            data = response.json().get('data', [])
            
            for fix in data:
                participants = fix.get('participants', [])
                local = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
                visita = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
                
                nombre_l = local.get('name', '')
                nombre_v = visita.get('name', '')

                if es_equipo_escoces(nombre_l):
                    partidos_finales.append({
                        'id': fix.get('id'),
                        'label': f"{nombre_l} vs {nombre_v}",
                        'fecha': fix.get('starting_at').split(' ')[0]
                    })

        # Imprimir tabla de IDs
        print(f"\n--- IDS PARA STATS: JORNADA 3 ---")
        print(f"{'ID PARTIDO':<12} | {'ENFRENTAMIENTO':<40} | {'FECHA'}")
        print("-" * 70)
        
        for p in partidos_finales:
            print(f"{p['id']:<12} | {p['label']:<40} | {p['fecha']}")
            
        return partidos_finales

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    lista_partidos = obtener_ids_partidos_j3()
