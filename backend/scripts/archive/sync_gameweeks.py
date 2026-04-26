"""
Sincronización de Jornadas y Partidos — Temporada 2025/2026
Descarga TODOS los partidos de la Scottish Premiership desde SportMonks,
los agrupa por jornada, y los guarda/actualiza en la BD (upsert).
NO borra datos existentes (player_match_stats, gameweek_lineups).

Basado en la lógica probada de prueba.py del usuario.
"""

import sys
import os
import requests
import time
from datetime import datetime
from collections import defaultdict

# Fix para emojis en consola Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Ajustar ruta para importar módulos del backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.models import Gameweek, Match, MatchStatus

# ==============================================================================
# CONFIGURACIÓN — Idéntica a prueba.py
# ==============================================================================
API_TOKEN = '8Jolb4HwJbTxrxBwYJWjndgAHXstanHw5rrrtqCB4f17SeV6uvHiJ8uYKGb1'
HOY = datetime.now().strftime('%Y-%m-%d')

# Los 12 equipos confirmados para la temporada 25/26
EQUIPOS_PREMIERSHIP = [
    "Dundee United", "St. Mirren", "Celtic", "Rangers", "Aberdeen",
    "Hearts", "Hibernian", "Dundee", "Motherwell", "Kilmarnock",
    "Livingston", "Falkirk"
]

# Rango de toda la temporada regular
PERIODOS = [
    ("2025-08-01", "2025-08-31"), ("2025-09-01", "2025-09-30"),
    ("2025-10-01", "2025-10-31"), ("2025-11-01", "2025-11-30"),
    ("2025-12-01", "2025-12-31"), ("2026-01-01", "2026-01-31"),
    ("2026-02-01", "2026-02-28"), ("2026-03-01", "2026-03-31"),
    ("2026-04-01", "2026-04-30"), ("2026-05-01", "2026-05-31")
]

# Máximo de jornadas de la fase regular (12 equipos = 33 jornadas)
MAX_GAMEWEEK = 33

# Mapa de nombres para normalizar variantes de la API
TEAM_NAME_MAP = {
    'Celtic': ['Celtic'],
    'Rangers': ['Rangers'],
    'Aberdeen': ['Aberdeen'],
    'Hearts': ['Hearts', 'Heart of Midlothian'],
    'Hibernian': ['Hibernian'],
    'Dundee': ['Dundee', 'Dundee FC'],
    'Dundee United': ['Dundee United', 'Dundee United Football Club'],
    'Motherwell': ['Motherwell'],
    'St. Mirren': ['St. Mirren', 'St Mirren'],
    'Kilmarnock': ['Kilmarnock'],
    'Livingston': ['Livingston'],
    'Falkirk': ['Falkirk'],
}


def es_equipo_activo(nombre):
    """Misma función que prueba.py"""
    for eq in EQUIPOS_PREMIERSHIP:
        if eq in nombre:
            return True
    return False


def normalize_team_name(api_name):
    """Normaliza el nombre de la API al nombre estándar de la BD"""
    for db_name, variants in TEAM_NAME_MAP.items():
        for variant in variants:
            if variant.lower() in api_name.lower():
                return db_name
    return api_name


def fetch_all_fixtures():
    """
    Obtiene TODOS los partidos de la temporada 25/26.
    Misma lógica exacta que prueba.py pero devolviendo datos estructurados.
    """
    base_url = "https://api.sportmonks.com/v3/football/fixtures/between"
    params = {
        'api_token': API_TOKEN,
        'include': 'participants;scores;round;state'
    }

    todos = []
    print(f"🚀 Descargando calendario de SportMonks (Hoy: {HOY})...")

    try:
        for inicio, fin in PERIODOS:
            page = 1
            while True:
                url = f"{base_url}/{inicio}/{fin}?page={page}"
                resp = requests.get(url, params=params)
                if resp.status_code != 200:
                    break

                data_json = resp.json()
                data = data_json.get('data', [])
                if not data:
                    break

                for fix in data:
                    p = fix.get('participants', [])
                    loc = next((x for x in p if x.get('meta', {}).get('location') == 'home'), {})
                    vis = next((x for x in p if x.get('meta', {}).get('location') == 'away'), {})

                    n_l = loc.get('name', '???')
                    n_v = vis.get('name', '???')

                    # Filtrar: solo los 12 equipos de la liga
                    if not (es_equipo_activo(n_l) or es_equipo_activo(n_v)):
                        continue

                    gl = gv = 0
                    marcador_detectado = False
                    for s in fix.get('scores', []):
                        if s.get('description') in ['CURRENT', 'FT', '2T', '1T']:
                            marcador_detectado = True
                            if s.get('participant_id') == loc.get('id'):
                                gl = s.get('score', {}).get('goals', 0)
                            if s.get('participant_id') == vis.get('id'):
                                gv = s.get('score', {}).get('goals', 0)

                    fecha_p = fix.get('starting_at', '')
                    r_name = fix.get('round', {}).get('name', '0')
                    round_num = int(r_name) if r_name.isdigit() else 0

                    if round_num == 0 or round_num > MAX_GAMEWEEK:
                        continue

                    todos.append({
                        'sportmonks_id': fix['id'],
                        'home_team': normalize_team_name(n_l),
                        'away_team': normalize_team_name(n_v),
                        'home_score': gl if marcador_detectado else None,
                        'away_score': gv if marcador_detectado else None,
                        'has_scores': marcador_detectado,
                        'round_num': round_num,
                        'kickoff': fecha_p
                    })

                if not data_json.get('pagination', {}).get('has_more', False):
                    break
                page += 1
                time.sleep(0.1)

    except Exception as e:
        print(f"❌ Error descargando datos: {e}")

    return todos


def sync_gameweeks():
    db = SessionLocal()
    fixtures = fetch_all_fixtures()
    print(f"✅ {len(fixtures)} partidos encontrados\n")

    # Agrupar por jornada
    gameweek_fixtures = defaultdict(list)
    for f in fixtures:
        gameweek_fixtures[f['round_num']].append(f)

    ahora = datetime.utcnow()

    # ─── 1. UPSERT JORNADAS ──────────────────────────────────────────
    print("🔄 Sincronizando Jornadas...")
    db_gameweeks = {gw.number: gw for gw in db.query(Gameweek).all()}

    gameweeks_dates = {}

    for round_num, fxs in gameweek_fixtures.items():
        dates = [
            datetime.strptime(fx['kickoff'][:19], '%Y-%m-%d %H:%M:%S')
            for fx in fxs if fx['kickoff']
        ]
        if not dates:
            continue

        start_date = min(dates)
        end_date = max(dates)
        # Una jornada está finalizada si su end_date ya pasó
        is_finished = end_date < ahora

        gameweeks_dates[round_num] = {
            'start_date': start_date,
            'end_date': end_date,
            'is_finished': is_finished,
            'fxs': fxs
        }

        if round_num in db_gameweeks:
            gw = db_gameweeks[round_num]
            gw.start_date = start_date
            gw.end_date = end_date
            gw.is_finished = is_finished
            gw.is_active = False
        else:
            gw = Gameweek(
                number=round_num,
                start_date=start_date,
                end_date=end_date,
                is_active=False,
                is_finished=is_finished
            )
            db.add(gw)
            db_gameweeks[round_num] = gw

    db.commit()

    # ─── 2. CALCULAR JORNADA ACTIVA ──────────────────────────────────
    print("⚙️  Calculando jornada activa...")
    active_gw_num = None

    sorted_gws = sorted(gameweeks_dates.items(), key=lambda x: x[0])

    for round_num, info in sorted_gws:
        # La jornada activa es la primera cuyo start_date está en el futuro
        if info['start_date'] > ahora:
            active_gw_num = round_num
            break

    # Si no hay ninguna futura, buscar la primera no finalizada
    if not active_gw_num:
        for round_num, info in sorted_gws:
            if not info['is_finished']:
                active_gw_num = round_num
                break

    if active_gw_num and active_gw_num in db_gameweeks:
        db_gameweeks[active_gw_num].is_active = True
        print(f"🏆 Jornada activa: GW {active_gw_num} (Inicio: {gameweeks_dates[active_gw_num]['start_date']})")
    else:
        print("🏁 Temporada finalizada — no hay jornada activa.")

    db.commit()

    # ─── 3. UPSERT PARTIDOS ──────────────────────────────────────────
    print("\n🔄 Sincronizando Partidos...")
    creados = 0
    actualizados = 0

    for gw_num, info in gameweeks_dates.items():
        gw_id = db_gameweeks[gw_num].id

        for fx in info['fxs']:
            kickoff_dt = datetime.strptime(fx['kickoff'][:19], '%Y-%m-%d %H:%M:%S') if fx['kickoff'] else None
            fecha_str = fx['kickoff'].split(' ')[0] if fx['kickoff'] else ''

            # Estado: FINALIZADO si tiene marcador O si la fecha ya pasó
            if fx['has_scores'] or fecha_str < HOY:
                status = MatchStatus.FINISHED
            else:
                status = MatchStatus.SCHEDULED

            db_match = db.query(Match).filter(Match.sportmonks_id == fx['sportmonks_id']).first()

            if db_match:
                db_match.home_score = fx['home_score']
                db_match.away_score = fx['away_score']
                db_match.status = status
                if kickoff_dt:
                    db_match.kickoff_time = kickoff_dt
                actualizados += 1
            else:
                new_match = Match(
                    sportmonks_id=fx['sportmonks_id'],
                    gameweek_id=gw_id,
                    home_team=fx['home_team'],
                    away_team=fx['away_team'],
                    home_score=fx['home_score'],
                    away_score=fx['away_score'],
                    status=status,
                    kickoff_time=kickoff_dt or ahora
                )
                db.add(new_match)
                creados += 1

    db.commit()
    print(f"✅ Partidos: {creados} creados, {actualizados} actualizados.")
    print("🚀 Sincronización completada con éxito.")
    db.close()


if __name__ == "__main__":
    sync_gameweeks()
