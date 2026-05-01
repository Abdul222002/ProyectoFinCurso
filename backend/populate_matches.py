"""
Script para poblar la BD con datos reales de partidos de la Scottish Premiership.
Usa la API de SportMonks v3 para obtener:
  1) Todas las jornadas y partidos ya jugados
  2) Stats de cada jugador en cada partido (lineups + details)
  3) Calcula fantasy points
  4) TODOS los jugadores de un equipo reciben un registro por partido,
     aunque no hayan sido convocados (stats a 0).
"""

import requests
import time
import logging
from datetime import datetime
from collections import defaultdict

# Silenciar SQLAlchemy
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)

from app.core.database import SessionLocal
from app.models.models import (
    Player, Gameweek, Match, PlayerMatchStats, MatchStatus
)

API_TOKEN = 'uE2hA7iHbThgr4DjSOXCZEMYK7mIja06CEM4RooUWltOIUjXad9hqU4DqcYp'
LEAGUE_ID = 501  # Scottish Premiership

PERIODOS = [
    ("2025-08-01", "2025-08-31"), ("2025-09-01", "2025-09-30"),
    ("2025-10-01", "2025-10-31"), ("2025-11-01", "2025-11-30"),
    ("2025-12-01", "2025-12-31"), ("2026-01-01", "2026-01-31"),
    ("2026-02-01", "2026-02-17"),
]

# =============================================
# MAPEO de type_id (numérico) de SportMonks v3 → campos de BD
# Obtenido directamente de la API con include=lineups.details.type
# =============================================
STAT_TYPE_MAP = {
    119: 'minutes_played',       # MINUTES_PLAYED
    118: 'rating',               # RATING
    52:  'goals',                # GOALS
    79:  'assists',              # ASSISTS
    84:  'yellow_cards',         # YELLOWCARDS
    83:  'red_cards',            # REDCARDS
    57:  'saves',                # SAVES
    86:  'shots_on_target',      # SHOTS_ON_TARGET
    42:  'shots_total',          # SHOTS_TOTAL
    101: 'clearances',           # CLEARANCES
    78:  'tackles',              # TACKLES
    100: 'interceptions',        # INTERCEPTIONS
    116: 'accurate_passes',      # ACCURATE_PASSES
    80:  'total_passes',         # PASSES
    106: 'duels_won',            # DUELS_WON
    56:  'fouls',                # FOULS
    109: 'dribbles',             # SUCCESSFUL_DRIBBLES
    99:  'crosses',              # ACCURATE_CROSSES
    27271: 'ball_recoveries',    # BALL_RECOVERY
    94:  'dispossessed',         # DISPOSSESSED
    27273: 'turnovers',          # POSSESSION_LOST
    121: 'turn_over',            # TURN_OVER
    580: 'chances_created',      # BIG_CHANCES_CREATED
    114: 'penalty_committed',    # PENALTIES_COMMITTED
    115: 'penalty_won',          # PENALTIES_WON
    88:  'goals_conceded_team',  # GOALS_CONCEDED
    1535: 'goals_conceded',      # GOALKEEPER_GOALS_CONCEDED
    117: 'key_passes',           # KEY_PASSES (extra)
}

# =============================================
# Mapeo equipo BD → nombres que usa SportMonks
# =============================================
TEAM_NAME_MAP = {
    'Celtic': ['Celtic'],
    'Rangers': ['Rangers'],
    'Aberdeen': ['Aberdeen'],
    'Hearts': ['Hearts', 'Heart of Midlothian'],
    'Hibernian': ['Hibernian'],
    'Dundee': ['Dundee', 'Dundee FC'],
    'Dundee United': ['Dundee United'],
    'Motherwell': ['Motherwell'],
    'St. Mirren': ['St. Mirren', 'St Mirren'],
    'Kilmarnock': ['Kilmarnock'],
    'Livingston': ['Livingston'],
    'Falkirk': ['Falkirk'],
    'Ross County': ['Ross County'],
    'St. Johnstone': ['St. Johnstone', 'St Johnstone'],
}


def normalize_team_name(api_name):
    """
    Convierte un nombre de equipo de la API al nombre que usamos en la BD.
    Usa una búsqueda por longitud descendente para evitar que 'Dundee' coincida con 'Dundee United'.
    """
    if not api_name:
        return ""
    
    api_name_lower = api_name.lower()
    
    # Creamos una lista de (variante, nombre_bd) y la ordenamos por longitud de variante (descendente)
    all_variants = []
    for db_name, api_variants in TEAM_NAME_MAP.items():
        for variant in api_variants:
            all_variants.append((variant.lower(), db_name))
    
    # Ordenar por longitud de la variante de forma descendente
    all_variants.sort(key=lambda x: len(x[0]), reverse=True)
    
    for variant_lower, db_name in all_variants:
        # Coincidencia exacta o palabra completa
        if variant_lower == api_name_lower:
            return db_name
        
        # Coincidencia de subcadena pero asegurando que sea una palabra completa o al menos la más larga
        if variant_lower in api_name_lower:
            return db_name
            
    return api_name


def calculate_fantasy_points(stats, position):
    """Calcula fantasy points con lógica corregida para Scottish Premiership"""
    pts = 0.0

    # 1. Presencia (Base)
    mins = stats.get('minutes_played', 0)
    if mins > 0:
        pts += 1
    if mins >= 60:
        pts += 1  # Total 2 pts por jugar 60+

    # 2. Goles (Depende de posición)
    goals = stats.get('goals', 0)
    if position == 'FWD':
        pts += goals * 4
    elif position == 'MID':
        pts += goals * 5
    elif position in ('DEF', 'GK'):
        pts += goals * 6

    # 3. Asistencias
    pts += stats.get('assists', 0) * 3

    # 4. Clean Sheet (Solo si jugó 60+)
    if stats.get('clean_sheet', False) and mins >= 60:
        if position in ('GK', 'DEF'):
            pts += 4
        elif position == 'MID':
            pts += 1

    # 5. Penalizaciones por goles (Solo GK/DEF)
    if position in ('GK', 'DEF'):
        gc = stats.get('goals_conceded_team', 0)
        if gc >= 2:
            pts -= (gc // 2) * 1

    # 6. Porteros (Saves)
    saves = stats.get('saves', 0)
    pts += (saves // 3) * 1

    # 7. Disciplina
    pts -= stats.get('yellow_cards', 0) * 1
    pts -= stats.get('red_cards', 0) * 3
    pts -= stats.get('penalty_miss', 0) * 2
    pts += stats.get('penalty_save', 0) * 5

    # 8. Bonus por rendimiento
    pts += stats.get('shots_on_target', 0) * 0.5
    pts += stats.get('chances_created', 0) * 1
    pts += (stats.get('tackles', 0) // 2) * 0.5

    # Rating de SportMonks (Bonus)
    rating = stats.get('rating', 0) or 0
    if rating >= 8.5:
        pts += 3
    elif rating >= 7.5:
        pts += 1

    return round(pts, 1)


def process_lineup_stats(lineup_entry):
    """Extrae y mapea todas las estadísticas de SportMonks v3.
    
    Formato real de la API:
    {
        "type_id": 119,  (numérico)
        "data": {"value": 90}
    }
    """
    stats = defaultdict(int)
    details = lineup_entry.get('details', [])

    for detail in details:
        type_id = detail.get('type_id')
        if type_id not in STAT_TYPE_MAP:
            continue

        field_name = STAT_TYPE_MAP[type_id]
        val = detail.get('data', {}).get('value', 0)

        if field_name == 'rating':
            stats[field_name] = float(val) if val else 0.0
        elif field_name == 'turn_over':
            # Acumular turn_over en turnovers si no hay possession_lost
            stats['turnovers'] = stats.get('turnovers', 0) + (int(val) if val else 0)
        else:
            stats[field_name] = int(val) if val else 0

    return stats


def fetch_all_fixtures():
    """Obtiene todos los partidos de la temporada (solo league_id=501)"""
    base_url = "https://api.sportmonks.com/v3/football/fixtures/between"
    all_fixtures = []

    for inicio, fin in PERIODOS:
        page = 1
        while True:
            url = f"{base_url}/{inicio}/{fin}"
            params = {
                'api_token': API_TOKEN,
                'include': 'participants;scores;round;state',
                'page': page
            }
            resp = requests.get(url, params=params)
            if resp.status_code != 200:
                print(f"  ⚠️ Error {resp.status_code} en {inicio}/{fin} page {page}")
                break

            data = resp.json().get('data', [])
            if not data:
                break

            for fix in data:
                if fix.get('league_id') != LEAGUE_ID:
                    continue

                participants = fix.get('participants', [])
                loc = next((x for x in participants if x.get('meta', {}).get('location') == 'home'), {})
                vis = next((x for x in participants if x.get('meta', {}).get('location') == 'away'), {})

                gl, gv, jugado = 0, 0, False
                for s in fix.get('scores', []):
                    if s.get('description') in ['CURRENT', 'FT']:
                        jugado = True
                        if s.get('participant_id') == loc.get('id'):
                            gl = s.get('score', {}).get('goals', 0)
                        if s.get('participant_id') == vis.get('id'):
                            gv = s.get('score', {}).get('goals', 0)

                r_name = fix.get('round', {}).get('name', '0')
                round_num = int(r_name) if r_name.isdigit() else 0

                home_name = normalize_team_name(loc.get('name', ''))
                away_name = normalize_team_name(vis.get('name', ''))

                all_fixtures.append({
                    'sportmonks_id': fix['id'],
                    'home_team': home_name,
                    'away_team': away_name,
                    'home_team_api_id': loc.get('id'),
                    'away_team_api_id': vis.get('id'),
                    'home_score': gl if jugado else None,
                    'away_score': gv if jugado else None,
                    'jugado': jugado,
                    'round_num': round_num,
                    'kickoff': fix.get('starting_at', ''),
                })

            if not resp.json().get('pagination', {}).get('has_more', False):
                break
            page += 1
            time.sleep(0.15)

    all_fixtures.sort(key=lambda x: (x['round_num'], x['kickoff']))
    return all_fixtures


def fetch_fixture_lineups(fixture_id):
    """Obtiene los lineups + details de un partido específico"""
    url = f"https://api.sportmonks.com/v3/football/fixtures/{fixture_id}"
    params = {
        'api_token': API_TOKEN,
        'include': 'lineups.details'
    }
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        return []
    data = resp.json().get('data', {})
    return data.get('lineups', [])


def main():
    db = SessionLocal()

    # ========================================
    # PASO 0: Limpiar datos anteriores
    # ========================================
    print("🗑️  Limpiando datos anteriores...")
    db.query(PlayerMatchStats).delete()
    db.query(Match).delete()
    db.query(Gameweek).delete()
    # Resetear acumuladores de jugadores
    db.query(Player).filter(Player.is_legend == False).update({
        Player.total_matches_played: 0,
        Player.sum_match_ratings: 0.0,
        Player.sum_fantasy_points: 0.0,
    })
    db.commit()
    print("✅ Datos limpiados")

    # ========================================
    # PASO 1: Cargar jugadores por equipo
    # ========================================
    players_all = db.query(Player).filter(
        Player.is_legend == False,
        Player.sportmonks_id != None
    ).all()

    sm_to_player = {p.sportmonks_id: p for p in players_all}

    # Agrupar jugadores por equipo (nombre en BD)
    team_players = defaultdict(list)
    for p in players_all:
        team_players[p.current_team].append(p)

    print(f"📊 {len(players_all)} jugadores cargados en {len(team_players)} equipos")
    for team, plist in sorted(team_players.items()):
        print(f"   {team}: {len(plist)} jugadores")

    # ========================================
    # PASO 2: Obtener todos los partidos
    # ========================================
    print("\n🔄 Obteniendo partidos de SportMonks...")
    fixtures = fetch_all_fixtures()
    jugados = [f for f in fixtures if f['jugado']]
    print(f"✅ {len(fixtures)} partidos totales, {len(jugados)} ya jugados")

    # ========================================
    # PASO 3: Crear gameweeks
    # ========================================
    print("\n🔄 Creando jornadas...")
    gameweek_map = {}
    rounds_seen = defaultdict(list)
    for f in fixtures:
        rounds_seen[f['round_num']].append(f)

    for round_num in sorted(rounds_seen.keys()):
        if round_num == 0:
            continue
        fxs = rounds_seen[round_num]
        dates = [fx['kickoff'][:10] for fx in fxs if fx['kickoff']]
        if not dates:
            continue
        start_date = min(dates)
        end_date = max(dates)
        is_finished = all(fx['jugado'] for fx in fxs)

        gw = Gameweek(
            number=round_num,
            start_date=datetime.strptime(start_date, '%Y-%m-%d'),
            end_date=datetime.strptime(end_date, '%Y-%m-%d'),
            is_active=False,
            is_finished=is_finished
        )
        db.add(gw)
        db.flush()
        gameweek_map[round_num] = gw.id

    db.commit()
    print(f"✅ {len(gameweek_map)} jornadas creadas")

    # ========================================
    # PASO 4: Crear partidos + stats
    # ========================================
    print("\n🔄 Creando partidos y stats de jugadores...")
    matches_created = 0
    stats_created = 0
    errors = 0

    for i, fx in enumerate(jugados):
        gw_id = gameweek_map.get(fx['round_num'])
        if not gw_id:
            continue

        # Crear el match
        match = Match(
            sportmonks_id=fx['sportmonks_id'],
            gameweek_id=gw_id,
            home_team=fx['home_team'],
            away_team=fx['away_team'],
            home_score=fx['home_score'],
            away_score=fx['away_score'],
            status=MatchStatus.FINISHED,
            kickoff_time=datetime.strptime(
                fx['kickoff'][:19], '%Y-%m-%d %H:%M:%S'
            ) if fx['kickoff'] else datetime.now()
        )
        db.add(match)
        db.flush()
        match_id = match.id
        matches_created += 1

        # Goles recibidos por cada equipo
        goals_conceded_home = fx['away_score'] or 0  # Local recibe los del visitante
        goals_conceded_away = fx['home_score'] or 0  # Visitante recibe los del local

        # Obtener lineups de la API
        try:
            lineups = fetch_fixture_lineups(fx['sportmonks_id'])
        except Exception as e:
            print(f"  ⚠️ Error lineup fixture {fx['sportmonks_id']}: {e}")
            lineups = []
            errors += 1

        # Procesar stats de los que SÍ aparecen en el lineup
        lineup_player_ids = set()
        lineup_stats = {}  # sportmonks_id → stats_dict

        for lineup_entry in lineups:
            player_sm_id = lineup_entry.get('player_id')
            if player_sm_id not in sm_to_player:
                continue

            lineup_player_ids.add(player_sm_id)
            stats_dict = process_lineup_stats(lineup_entry)

            # Determinar si es home o away
            team_id_in_lineup = lineup_entry.get('team_id')
            if team_id_in_lineup == fx['home_team_api_id']:
                received = goals_conceded_home
            elif team_id_in_lineup == fx['away_team_api_id']:
                received = goals_conceded_away
            else:
                # Fallback: intentar usar lo que venga de la API
                received = stats_dict.get('goals_conceded_team', 0)

            stats_dict['goals_conceded_team'] = received
            lineup_stats[player_sm_id] = stats_dict

        # Ahora crear registros para TODOS los jugadores de los equipos del partido
        home_team_name = fx['home_team']
        away_team_name = fx['away_team']

        teams_in_match = [
            (home_team_name, goals_conceded_home),
            (away_team_name, goals_conceded_away),
        ]

        for team_name, team_gc in teams_in_match:
            players_in_team = team_players.get(team_name, [])

            for player in players_in_team:
                # ¿Tiene stats del lineup?
                if player.sportmonks_id in lineup_stats:
                    st = lineup_stats[player.sportmonks_id]
                else:
                    # No convocado → registro vacío con 0 en todo
                    st = defaultdict(int)
                    st['goals_conceded_team'] = team_gc

                # Clean sheet
                mins = st.get('minutes_played', 0)
                clean_sheet = (team_gc == 0 and mins >= 60)
                st['clean_sheet'] = clean_sheet

                # Total losses
                total_losses = st.get('dispossessed', 0) + st.get('turnovers', 0)

                # Fantasy points
                pos = player.position.value
                fp = calculate_fantasy_points(st, pos)

                pms = PlayerMatchStats(
                    player_id=player.id,
                    match_id=match_id,
                    minutes_played=st.get('minutes_played', 0),
                    rating=st.get('rating') if st.get('rating') else None,
                    goals=st.get('goals', 0),
                    assists=st.get('assists', 0),
                    chances_created=st.get('chances_created', 0),
                    clean_sheet=clean_sheet,
                    goals_conceded=st.get('goals_conceded', 0),
                    goals_conceded_team=team_gc,
                    saves=st.get('saves', 0),
                    clearances=st.get('clearances', 0),
                    penalty_miss=st.get('penalty_miss', 0),
                    penalty_save=st.get('penalty_save', 0),
                    penalty_won=st.get('penalty_won', 0),
                    penalty_committed=st.get('penalty_committed', 0),
                    yellow_cards=st.get('yellow_cards', 0),
                    red_cards=st.get('red_cards', 0),
                    shots_on_target=st.get('shots_on_target', 0),
                    dribbles=st.get('dribbles', 0),
                    crosses=st.get('crosses', 0),
                    ball_recoveries=st.get('ball_recoveries', 0),
                    dispossessed=st.get('dispossessed', 0),
                    possession_lost=st.get('turnovers', 0),
                    turnovers=st.get('turnovers', 0),
                    total_losses=total_losses,
                    shots_total=st.get('shots_total', 0),
                    accurate_passes=st.get('accurate_passes', 0),
                    total_passes=st.get('total_passes', 0),
                    tackles=st.get('tackles', 0),
                    interceptions=st.get('interceptions', 0),
                    duels_won=st.get('duels_won', 0),
                    fouls=st.get('fouls', 0),
                    fantasy_points=fp,
                    created_at=datetime.now()
                )
                db.add(pms)
                stats_created += 1

                # Actualizar acumuladores del Player
                player.total_matches_played += 1
                if st.get('rating'):
                    player.sum_match_ratings += float(st['rating'])
                player.sum_fantasy_points += fp

        # Commit por partido
        db.commit()

        if (i + 1) % 10 == 0 or (i + 1) == len(jugados):
            print(f"  [{i+1}/{len(jugados)}] {matches_created} matches, {stats_created} stats...")

        time.sleep(0.2)

    print(f"\n{'='*60}")
    print(f"✅ RESUMEN FINAL:")
    print(f"   Jornadas:           {len(gameweek_map)}")
    print(f"   Partidos creados:   {matches_created}")
    print(f"   Stats de jugadores: {stats_created}")
    print(f"   Errores API:        {errors}")
    print(f"{'='*60}")

    # Top 10 fantasy
    top = db.query(Player).filter(
        Player.is_legend == False,
        Player.total_matches_played > 0
    ).order_by(Player.sum_fantasy_points.desc()).limit(10).all()

    print("\n🏆 TOP 10 jugadores por Fantasy Points:")
    for i, p in enumerate(top, 1):
        avg_fp = p.sum_fantasy_points / p.total_matches_played if p.total_matches_played > 0 else 0
        print(f"  {i}. {p.name} ({p.current_team}) — "
              f"{p.sum_fantasy_points:.0f} pts total, {avg_fp:.1f} avg, "
              f"{p.total_matches_played} partidos")

    # Verificación: stats por equipo
    print("\n📋 Stats por equipo:")
    for team in sorted(team_players.keys()):
        n_players = len(team_players[team])
        # Contar stats de ese equipo
        total_stats = sum(p.total_matches_played for p in team_players[team])
        avg_matches = total_stats / n_players if n_players > 0 else 0
        print(f"  {team}: {n_players} jugadores × {avg_matches:.0f} partidos avg = {total_stats} registros")

    db.close()


if __name__ == '__main__':
    main()
