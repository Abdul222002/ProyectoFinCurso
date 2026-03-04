import requests
import time
from datetime import datetime

# ==============================================================================
# CONFIGURACIÓN ACTUALIZADA
# ==============================================================================
API_TOKEN = '8Jolb4HwJbTxrxBwYJWjndgAHXstanHw5rrrtqCB4f17SeV6uvHiJ8uYKGb1'
HOY = datetime.now().strftime('%Y-%m-%d') 

# Lista de los 12 equipos confirmados para la temporada 25/26
EQUIPOS_PREMIERSHIP = [
    "Dundee United", "St. Mirren", "Celtic", "Rangers", "Aberdeen",
    "Hearts", "Hibernian", "Dundee", "Motherwell", "Kilmarnock",
    "Livingston", "Falkirk"
]

def es_equipo_activo(nombre):
    for eq in EQUIPOS_PREMIERSHIP:
        if eq in nombre: return True
    return False

def obtener_calendario_2026():
    base_url = "https://api.sportmonks.com/v3/football/fixtures/between"
    
    # Rango de toda la temporada regular
    periodos = [
        ("2025-08-01", "2025-08-31"), ("2025-09-01", "2025-09-30"),
        ("2025-10-01", "2025-10-31"), ("2025-11-01", "2025-11-30"),
        ("2025-12-01", "2025-12-31"), ("2026-01-01", "2026-01-31"),
        ("2026-02-01", "2026-02-28"), ("2026-03-01", "2026-03-31"),
        ("2026-04-01", "2026-04-30"), ("2026-05-01", "2026-05-31")
    ]

    params = {
        'api_token': API_TOKEN, 
        'include': 'participants;scores;round;state'
    }
    
    partidos_totales = []
    print(f"🚀 Iniciando consulta con nueva API Key (Hoy: {HOY})...")

    try:
        for inicio, fin in periodos:
            page = 1
            while True:
                url = f"{base_url}/{inicio}/{fin}?page={page}"
                response = requests.get(url, params=params)
                if response.status_code != 200: break

                data_json = response.json()
                data = data_json.get('data', [])
                if not data: break
                
                for fix in data:
                    p = fix.get('participants', [])
                    loc = next((x for x in p if x.get('meta', {}).get('location') == 'home'), {})
                    vis = next((x for x in p if x.get('meta', {}).get('location') == 'away'), {})
                    
                    n_l = loc.get('name', '???')
                    n_v = vis.get('name', '???')

                    # Filtrar por los 12 equipos de la liga
                    if es_equipo_activo(n_l) or es_equipo_activo(n_v):
                        gl = gv = 0
                        marcador_detectado = False
                        scores = fix.get('scores', [])
                        for s in scores:
                            if s.get('description') in ['CURRENT', 'FT', '2T', '1T']:
                                marcador_detectado = True
                                if s.get('participant_id') == loc.get('id'): gl = s.get('score', {}).get('goals', 0)
                                if s.get('participant_id') == vis.get('id'): gv = s.get('score', {}).get('goals', 0)
                        
                        fecha_p = fix.get('starting_at').split(' ')[0]
                        
                        # Lógica de estado manual corregida
                        if marcador_detectado or fecha_p < HOY:
                            estado = 'FINALIZADO'
                            res_display = f"{gl}-{gv}"
                        else:
                            estado = 'PENDIENTE'
                            res_display = "vs"

                        r_name = fix.get('round', {}).get('name', '??')
                        partidos_totales.append({
                            'jornada': int(r_name) if r_name.isdigit() else 99,
                            'j_str': r_name,
                            'id': fix.get('id'),
                            'estado': estado,
                            'fecha': fecha_p,
                            'enfrentamiento': f"{n_l:<18} vs {n_v:>18}",
                            'resultado': res_display
                        })
                
                if not data_json.get('pagination', {}).get('has_more', False): break
                page += 1
                time.sleep(0.1)

        # Ordenar por jornada y fecha
        partidos_totales.sort(key=lambda x: (x['jornada'], x['fecha']))
        
        print("\n" + "="*105)
        print(f"{'JOR.':<5} | {'ID PARTIDO':<12} | {'ESTADO':<12} | {'FECHA':<12} | {'ENFRENTAMIENTO':<43} | {'RES'}")
        print("="*105)

        for p in partidos_totales:
            print(f"{p['j_str']:<5} | {p['id']:<12} | {p['estado']:<12} | {p['fecha']:<12} | {p['enfrentamiento']:<43} | {p['resultado']}")

        print(f"\n✅ Proceso completado: {len(partidos_totales)}/198 partidos encontrados.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    obtener_calendario_2026()