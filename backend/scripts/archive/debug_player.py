"""
DEBUG ESPECÍFICO: Mahamadou Susoho
Ver EXACTAMENTE qué datos se extraen y cómo se calculan los puntos
"""

import os
import requests
from dotenv import load_dotenv
from enum import Enum
import math

load_dotenv()

API_TOKEN = os.getenv('SPORTMONKS_API_KEY')
FIXTURE_ID = 19428171

class Position(Enum):
    GK = "Portero"
    DEF = "Defensa"
    MID = "Mediocentro"
    FWD = "Delantero"

url = f"https://api.sportmonks.com/v3/football/fixtures/{FIXTURE_ID}"
params = {
    "api_token": API_TOKEN,
    "include": "lineups.details.type;participants;scores"
}

print("\n" + "="*80)
print("🔍 DEBUG: Mahamadou Susoho")
print("="*80 + "\n")

response = requests.get(url, params=params, timeout=30)
data = response.json().get('data', {})
lineups = data.get('lineups', [])

# Buscar a Mahamadou Susoho
for player_entry in lineups:
    if "Mahamadou Susoho" in player_entry.get('player_name', ''):
        
        print(f"✅ JUGADOR ENCONTRADO: {player_entry.get('player_name')}\n")
        print(f"Position ID: {player_entry.get('type_id')}")
        print(f"Participant ID: {player_entry.get('participant_id')}\n")
        
        # Extraer TODOS los detalles
        details = player_entry.get('details', [])
        
        print(f"📊 TODAS LAS ESTADÍSTICAS CRUDAS ({len(details)} campos):")
        print("-" * 80)
        
        stats_encontradas = {}
        
        for stat in details:
            type_info = stat.get('type', {})
            developer_name = type_info.get('developer_name', '')
            data_wrapper = stat.get('data', {})
            valor = data_wrapper.get('value')
            
            if valor is not None and valor != 0:
                stats_encontradas[developer_name] = valor
                print(f"  {developer_name:<35} = {valor}")
        
        print("\n" + "="*80)
        print("🧮 CÁLCULO DE PUNTOS PASO A PASO")
        print("="*80 + "\n")
        
        puntos_total = 0
        
        # 1. Minutos
        minutos = stats_encontradas.get('MINUTES_PLAYED', 0)
        print(f"1. MINUTOS JUGADOS: {minutos} min")
        if minutos >= 60:
            puntos_minutos = 2
            print(f"   ✅ {minutos} >= 60 → +2 puntos")
        else:
            puntos_minutos = 1
            print(f"   ⚠️  {minutos} < 60 → +1 punto")
        puntos_total += puntos_minutos
        print(f"   SUBTOTAL: {puntos_total} puntos\n")
        
        # 2. Goles
        goles = stats_encontradas.get('GOALS', 0)
        print(f"2. GOLES: {goles}")
        puntos_goles = int(goles) * 4  # Delantero
        print(f"   ✅ {goles} gol(es) × 4 (delantero) = +{puntos_goles} puntos")
        puntos_total += puntos_goles
        print(f"   SUBTOTAL: {puntos_total} puntos\n")
        
        # 3. Asistencias
        asistencias = stats_encontradas.get('ASSISTS', 0)
        chances_created = stats_encontradas.get('BIG_CHANCES_CREATED', 0)
        print(f"3. ASISTENCIAS:")
        print(f"   - Asistencias de gol: {asistencias}")
        print(f"   - Ocasiones creadas: {chances_created}")
        puntos_asist = int(asistencias) * 3 + int(chances_created) * 1
        print(f"   ✅ {asistencias}×3 + {chances_created}×1 = +{puntos_asist} puntos")
        puntos_total += puntos_asist
        print(f"   SUBTOTAL: {puntos_total} puntos\n")
        
        # 4. Nota
        rating = stats_encontradas.get('RATING', 0)
        if rating:
            rating_float = float(rating)
            print(f"4. NOTA DEL PARTIDO: {rating_float}")
            
            if rating_float >= 8.5:
                puntos_rating = 4
                print(f"   ✅ {rating_float} >= 8.5 → +4 puntos (máximo)")
            elif rating_float >= 5.0:
                puntos_rating = (rating_float - 5.0) * (4.0 / 3.5)
                print(f"   ✅ Fórmula lineal: ({rating_float} - 5.0) × (4/3.5) = +{puntos_rating:.2f} puntos")
            else:
                puntos_rating = 0
                print(f"   ❌ {rating_float} < 5.0 → 0 puntos")
            
            puntos_rating_redondeado = round(puntos_rating)
            print(f"   REDONDEADO: +{puntos_rating_redondeado} puntos")
            puntos_total += puntos_rating_redondeado
            print(f"   SUBTOTAL: {puntos_total} puntos\n")
        
        # 5. Tarjetas
        amarillas = stats_encontradas.get('YELLOWCARDS', 0)
        rojas = stats_encontradas.get('REDCARDS', 0)
        print(f"5. TARJETAS:")
        print(f"   - Amarillas: {amarillas}")
        print(f"   - Rojas: {rojas}")
        puntos_tarjetas = -(int(amarillas) * 1) - (int(rojas) * 3)
        if puntos_tarjetas < 0:
            print(f"   ❌ -{abs(puntos_tarjetas)} puntos")
        else:
            print(f"   ✅ Sin penalización")
        puntos_total += puntos_tarjetas
        print(f"   SUBTOTAL: {puntos_total} puntos\n")
        
        # 6. Acumuladores
        tiros = stats_encontradas.get('SHOTS_ON_TARGET', 0)
        regates = stats_encontradas.get('SUCCESSFUL_DRIBBLES', 0)
        cruces = stats_encontradas.get('ACCURATE_CROSSES', 0)
        recuperaciones = stats_encontradas.get('BALL_RECOVERY', 0)
        despejes = stats_encontradas.get('CLEARANCES', 0)
        
        print(f"6. ACUMULADORES:")
        print(f"   - Tiros a puerta: {tiros} → {math.floor(int(tiros)/2)} × 1 = +{math.floor(int(tiros)/2)} pts")
        print(f"   - Regates: {regates} → {math.floor(int(regates)/2)} × 1 = +{math.floor(int(regates)/2)} pts")
        print(f"   - Cruces: {cruces} → {math.floor(int(cruces)/2)} × 1 = +{math.floor(int(cruces)/2)} pts")
        print(f"   - Recuperaciones: {recuperaciones} → {math.floor(int(recuperaciones)/5)} × 1 = +{math.floor(int(recuperaciones)/5)} pts")
        print(f"   - Despejes: {despejes} → {math.floor(int(despejes)/3)} × 1 = +{math.floor(int(despejes)/3)} pts")
        
        puntos_acum = (math.floor(int(tiros)/2) + math.floor(int(regates)/2) + 
                       math.floor(int(cruces)/2) + math.floor(int(recuperaciones)/5) + 
                       math.floor(int(despejes)/3))
        print(f"   TOTAL ACUMULADORES: +{puntos_acum} puntos")
        puntos_total += puntos_acum
        print(f"   SUBTOTAL: {puntos_total} puntos\n")
        
        # 7. Pérdidas
        dispossessed = stats_encontradas.get('DISPOSSESSED', 0)
        possession_lost = stats_encontradas.get('POSSESSION_LOST', 0)
        turnovers = stats_encontradas.get('TURN_OVER', 0)
        total_perdidas = int(dispossessed) + int(possession_lost) + int(turnovers)
        
        print(f"7. PÉRDIDAS DE BALÓN:")
        print(f"   - Despo poseído: {dispossessed}")
        print(f"   - Posesión perdida: {possession_lost}")
        print(f"   - Pérdidas: {turnovers}")
        print(f"   TOTAL: {total_perdidas} pérdidas")
        
        # Delantero: cada 12
        penalizacion_perdidas = -math.floor(total_perdidas / 12)
        if penalizacion_perdidas < 0:
            print(f"   ❌ {total_perdidas} ÷ 12 = {penalizacion_perdidas} puntos (delantero)")
        else:
            print(f"   ✅ Menos de 12 pérdidas → 0 penalización")
        puntos_total += penalizacion_perdidas
        print(f"   SUBTOTAL: {puntos_total} puntos\n")
        
        print("="*80)
        print(f"🎯 PUNTOS TOTALES: {puntos_total}")
        print("="*80 + "\n")
        
        print("DESGLOSE ESPERADO:")
        print(f"  Minutos (90): {puntos_minutos}")
        print(f"  Goles (1×4): {puntos_goles}")
        print(f"  Nota (7.0): ~2")
        print(f"  TOTAL MÍNIMO ESPERADO: ~8 puntos")
        print(f"  TOTAL CALCULADO: {puntos_total} puntos")
        
        break
