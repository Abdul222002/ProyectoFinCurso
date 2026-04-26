"""Verificacion final de precios y rarezas"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("=" * 80)
print("VERIFICACION FINAL - PRECIOS Y RAREZAS")
print("=" * 80 + "\n")

# Rarezas
result = db.execute(text("""
    SELECT base_rarity, COUNT(*) as count,
           MIN(overall_rating) as min_ovr,
           MAX(overall_rating) as max_ovr
    FROM players
    GROUP BY base_rarity
    ORDER BY 
        CASE base_rarity
            WHEN 'GOLD' THEN 1
            WHEN 'SILVER' THEN 2
            WHEN 'BRONZE' THEN 3
        END
"""))

print("RAREZAS:")
total = 0
for row in result:
    total += row[1]
    
for row in db.execute(text("""
    SELECT base_rarity, COUNT(*) as count,
           MIN(overall_rating) as min_ovr,
           MAX(overall_rating) as max_ovr
    FROM players
    GROUP BY base_rarity
    ORDER BY 
        CASE base_rarity
            WHEN 'GOLD' THEN 1
            WHEN 'SILVER' THEN 2
            WHEN 'BRONZE' THEN 3
        END
""")).fetchall():
    pct = (row[1] / total) * 100
    print(f"  {row[0]}: {row[1]} ({pct:.1f}%) - OVR {row[2]}-{row[3]}")

# Precios
result = db.execute(text("""
    SELECT AVG(current_price), MIN(current_price), MAX(current_price)
    FROM players
"""))
stats = result.fetchone()
print(f"\nPRECIOS:")
print(f"  Promedio: EUR {stats[0]:,.0f}")
print(f"  Minimo: EUR {stats[1]:,.0f}")
print(f"  Maximo: EUR {stats[2]:,.0f}")

# Top 10
print("\n" + "=" * 80)
print("TOP 10 JUGADORES:")
print("=" * 80 + "\n")

result = db.execute(text("""
    SELECT name, position, overall_rating, current_team, base_rarity, current_price
    FROM players
    ORDER BY overall_rating DESC, current_price DESC
    LIMIT 10
"""))

for i, row in enumerate(result, 1):
    precio_m = row[5] / 1000000
    print(f"{i}. {row[0]} ({row[1]}) - OVR {row[2]} [{row[4]}]")
    print(f"   Equipo: {row[3]}")
    print(f"   Precio: EUR {precio_m:.1f}M\n")

db.close()
