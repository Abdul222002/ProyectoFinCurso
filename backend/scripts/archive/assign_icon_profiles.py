"""
Script: Asignar perfiles de puntuación a los 99 iconos
Ejecutar UNA VEZ para configurar min_fantasy, max_fantasy y scoring_profile.
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.models import Player

# ──────────────────────────────────────────────────────────────────
# PERFILES:
#   LEGEND   - Siempre cumple. Suelo alto. Nunca 0. (Pelé, Messi, C.Ronaldo)
#   MAESTRO  - Alta calidad regular, algún bajón puntual. Min 2-3 (Zidane, Henry)
#   RELIABLE - Distribución estrecha, muy predecible. Min sólido. (Maldini, Xavi)
#   VOLCANO  - Bimodal: 0 o cerca del max. Min 0, techo alto.  (Maradona, Ronaldinho)
#   CURSED   - 35% hace 0, 45% épico, 20% medio. (Ronaldo Nazário, Kaká)
# ──────────────────────────────────────────────────────────────────

# (name_fragment, scoring_profile, min_fantasy, max_fantasy)
ICON_PROFILES = [
    # OVR 99
    ("Pel",              "LEGEND",   9,  28),
    ("Maradona",         "VOLCANO",  0,  26),
    ("Messi",            "LEGEND",  10,  27),

    # OVR 97
    ("Zinedine Zidane",  "MAESTRO",  6,  23),

    # OVR 96
    ("Cristiano Ronaldo","LEGEND",  10,  26),
    ("Ronaldinho",       "VOLCANO",  0,  24),
    ("Ronaldo Naz",      "CURSED",   0,  26),

    # OVR 95
    ("Beckenbauer",      "LEGEND",   5,  17),
    ("Cruyff",           "MAESTRO",  5,  22),
    ("Di St",            "LEGEND",   8,  24),

    # OVR 94
    ("Eus",              "MAESTRO",  5,  22),
    ("Pusk",             "LEGEND",   7,  23),
    ("Garrincha",        "VOLCANO",  0,  24),
    ("George Best",      "CURSED",   0,  23),
    ("Gerd M",           "LEGEND",   7,  23),
    ("van Basten",       "CURSED",   0,  22),
    ("Platini",          "MAESTRO",  5,  21),
    ("Maldini",          "RELIABLE", 4,  14),

    # OVR 93
    ("Nesta",            "RELIABLE", 3,  13),
    ("Bobby Charlton",   "LEGEND",   6,  20),
    ("Cafu",             "RELIABLE", 3,  16),
    ("Cannavaro",        "RELIABLE", 3,  14),
    ("Baresi",           "RELIABLE", 3,  13),
    ("Meazza",           "MAESTRO",  4,  21),
    ("Casillas",         "RELIABLE", 4,  10),
    ("Yashin",           "RELIABLE", 3,  11),
    ("Matth",            "LEGEND",   5,  20),
    ("Roberto Carlos",   "VOLCANO",  0,  20),
    ("Henry",            "MAESTRO",  5,  22),
    ("Xavi",             "RELIABLE", 6,  18),

    # OVR 92
    ("Del Piero",        "MAESTRO",  4,  20),
    ("Pirlo",            "RELIABLE", 5,  17),
    ("Iniesta",          "MAESTRO",  5,  20),
    ("Bergkamp",         "MAESTRO",  5,  20),
    ("Dino Zoff",        "RELIABLE", 2,  10),
    ("Totti",            "MAESTRO",  5,  19),
    ("Buffon",           "RELIABLE", 3,  10),
    ("Modri",            "MAESTRO",  5,  19),
    ("Laudrup",          "MAESTRO",  4,  19),
    ("Oliver Kahn",      "RELIABLE", 2,  11),
    ("Schmeichel",       "RELIABLE", 2,  10),
    ("Lahm",             "RELIABLE", 3,  15),
    ("Rivaldo",          "VOLCANO",  0,  21),
    ("Rom",              "VOLCANO",  0,  20),
    ("Gullit",           "MAESTRO",  4,  20),
    ("van Dijk",         "RELIABLE", 3,  14),

    # OVR 91
    ("Puyol",            "RELIABLE", 3,  14),
    ("Seedorf",          "MAESTRO",  4,  19),
    ("Dani Alves",       "MAESTRO",  3,  16),
    ("Cantona",          "VOLCANO",  0,  20),
    ("Lampard",          "MAESTRO",  5,  21),
    ("Rijkaard",         "MAESTRO",  4,  18),
    ("Hagi",             "VOLCANO",  0,  19),
    ("Gordon Banks",     "RELIABLE", 3,  10),
    ("Jaap Stam",        "RELIABLE", 3,  12),
    ("Zanetti",          "RELIABLE", 3,  14),
    ("Kak",              "CURSED",   0,  20),
    ("Benzema",          "MAESTRO",  5,  20),
    ("Thuram",           "RELIABLE", 3,  13),
    ("Su",               "VOLCANO",  0,  21),
    ("Vieira",           "MAESTRO",  4,  19),
    ("Scholes",          "RELIABLE", 5,  19),
    ("Nedv",             "MAESTRO",  4,  19),
    ("Ra",               "RELIABLE", 5,  19),
    ("Lewandowski",      "RELIABLE", 6,  21),
    ("Sergio Ramos",     "VOLCANO",  0,  16),
    ("Gerrard",          "VOLCANO",  0,  22),
    ("Thiago Silva",     "RELIABLE", 3,  13),
    ("Rooney",           "MAESTRO",  5,  20),
    ("Ibrahimovi",       "VOLCANO",  0,  21),

    # OVR 90
    ("Drogba",           "VOLCANO",  0,  20),
    ("Piqu",             "MAESTRO",  2,  13),
    ("Hugo S",           "LEGEND",   5,  20),
    ("John Terry",       "RELIABLE", 2,  12),
    ("Dalglish",         "MAESTRO",  4,  19),
    ("Marcelo",          "VOLCANO",  0,  17),
    ("Ballack",          "MAESTRO",  4,  19),
    ("Vidic",            "RELIABLE", 2,  13),
    ("Pepe",             "VOLCANO",  0,  14),
    ("Varane",           "RELIABLE", 3,  13),
    ("Rio Ferdinand",    "RELIABLE", 2,  13),
    ("Roy Keane",        "VOLCANO",  0,  18),
    ("van Nistelrooy",   "RELIABLE", 5,  20),
    ("Eto",              "MAESTRO",  5,  20),
    ("Ag",               "VOLCANO",  0,  20),
    ("Socrates",         "MAESTRO",  4,  18),
    ("Kompany",          "RELIABLE", 2,  13),
    ("Zinedine Yazid",   "MAESTRO",  5,  20),

    # OVR 89 / 88 / 87
    ("Ashley Cole",      "RELIABLE", 2,  12),
    ("Schweinsteiger",   "MAESTRO",  3,  17),
    ("T",                "VOLCANO",  0,  19),   # Tévez
    ("David Villa",      "RELIABLE", 4,  18),
    ("Fernando Torres",  "CURSED",   0,  19),
    ("Zola",             "MAESTRO",  4,  18),
    ("Ian Rush",         "RELIABLE", 5,  19),
    ("de Ligt",          "MAESTRO",  2,  12),
    ("Sol Campbell",     "RELIABLE", 2,  12),
    ("Sneijder",         "VOLCANO",  0,  18),
    ("Ledley King",      "CURSED",   0,  11),
]


def assign_profiles():
    db = SessionLocal()
    updated = 0
    not_found = []

    try:
        icons = db.query(Player).filter(Player.is_legend == True).all()
        print(f"\n🏆 Total iconos en BD: {len(icons)}\n")

        for icon in icons:
            matched = None
            for (fragment, profile, min_f, max_f) in ICON_PROFILES:
                if fragment.lower() in icon.name.lower():
                    matched = (profile, min_f, max_f)
                    break

            if matched:
                icon.scoring_profile = matched[0]
                icon.min_fantasy = matched[1]
                icon.max_fantasy = matched[2]
                updated += 1
                print(f"  ✅ {icon.name:35s} → {matched[0]:10s} [{matched[1]:2d} – {matched[2]:2d}]")
            else:
                not_found.append(icon.name)

        db.commit()
        print(f"\n✅ {updated} iconos actualizados.")

        if not_found:
            print(f"\n⚠️  Sin perfil asignado ({len(not_found)}):")
            for n in not_found:
                print(f"   - {n}")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback; traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    assign_profiles()
