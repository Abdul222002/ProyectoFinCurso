import sys
import os
sys.path.append(os.path.abspath("backend"))

from app.core.database import SessionLocal
from app.models.models import Match

db = SessionLocal()

# Lista de equipos que juegan contra Dundee United normalmente 
# y que ahora mismo pueden estar mal etiquetados como contra "Dundee"
DUNDEE_UNITED_OPPONENTS = ['Kilmarnock', 'Hearts', 'Hibernian', 'Falkirk']

matches_to_fix = db.query(Match).filter(
    (Match.home_team == 'Dundee') | (Match.away_team == 'Dundee')
).all()

fixed_count = 0
for m in matches_to_fix:
    # Si el rival es uno de los típicos del Dundee United, cambiamos "Dundee" por "Dundee United"
    if m.home_team == 'Dundee' and m.away_team in DUNDEE_UNITED_OPPONENTS:
        m.home_team = 'Dundee United'
        fixed_count += 1
    elif m.away_team == 'Dundee' and m.home_team in DUNDEE_UNITED_OPPONENTS:
        m.away_team = 'Dundee United'
        fixed_count += 1
    # Caso especial: Dundee vs Dundee (que es Dundee vs Dundee United realmente)
    elif m.home_team == 'Dundee' and m.away_team == 'Dundee':
        # En la J21 fue Dundee vs Dundee United (0-1)
        # Por los datos, el marcador 0-1 sugiere que el visitante era el que ganó.
        # Vamos a poner el segundo como Dundee United
        m.away_team = 'Dundee United'
        fixed_count += 1

if fixed_count > 0:
    db.commit()
    print(f"✅ Limpieza completada: Se han corregido {fixed_count} partidos.")
else:
    print("ℹ️ No se encontraron partidos que necesitaran corrección inmediata.")

db.close()
