"""Verificacion simple de la BD"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# OVR range
result = db.execute(text("SELECT MIN(overall_rating), MAX(overall_rating), AVG(overall_rating) FROM players")).fetchone()
print(f"OVR Range: {result[0]}-{result[1]} (promedio: {result[2]:.1f})\n")

# Posiciones
result = db.execute(text("SELECT position, COUNT(*) FROM players GROUP BY position ORDER BY position"))
print("Posiciones:")
for r in result:
    print(f"  {r[0]}: {r[1]}")

# Nacionalidades
print("\nTop 5 nacionalidades:")
result = db.execute(text("SELECT nationality, COUNT(*) FROM players GROUP BY nationality ORDER BY COUNT(*) DESC LIMIT 5"))
for r in result:
    print(f"  {r[0]}: {r[1]}")

# Rarezas
print("\nRarezas:")
result = db.execute(text("SELECT base_rarity, COUNT(*) FROM players GROUP BY base_rarity"))
for r in result:
    print(f"  {r[0]}: {r[1]}")

# Top 10
print("\nTop 10 mejores jugadores:")
result = db.execute(text("SELECT name, position, overall_rating, current_team, current_price FROM players ORDER BY overall_rating DESC LIMIT 10"))
for i, r in enumerate(result, 1):
    print(f"{i}. {r[0]} ({r[1]}) - OVR {r[2]} - {r[3]}")
    print(f"   Precio: EUR {r[4]:,.0f}\n")

db.close()
