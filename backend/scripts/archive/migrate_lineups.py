from sqlalchemy import create_engine, text
import sys

DATABASE_URL = "mysql+pymysql://root:@localhost:3306/ultimate_fantasy_legends"
engine = create_engine(DATABASE_URL)

def migrate():
    try:
        with engine.connect() as conn:
            print("--- Iniciando Migración de Alineaciones (Versión Robustecida) ---")
            
            # Limpiar tabla por si hubo intentos previos (opcional o preventivo)
            conn.execute(text("DELETE FROM gameweek_lineup_players"))
            
            # 1. Obtener todas las alineaciones
            lineups = conn.execute(text("SELECT id, player_ids FROM gameweek_lineups")).fetchall()
            print(f"Encontradas {len(lineups)} alineaciones para procesar.")
            
            # 2. Obtener todos los IDs de user_cards válidos
            valid_cards = conn.execute(text("SELECT id FROM user_cards")).fetchall()
            valid_card_ids = {row[0] for row in valid_cards}
            
            total_inserted = 0
            skipped_ids = []
            
            for lineup_id, player_ids_str in lineups:
                if not player_ids_str or player_ids_str.strip() == "":
                    continue
                
                parts = [p.strip() for p in player_ids_str.split(",") if p.strip()]
                
                for p_id_str in parts:
                    try:
                        p_id = int(p_id_str)
                    except ValueError:
                        print(f"❌ ERROR: ID no numérico en lineup {lineup_id}: '{p_id_str}'")
                        continue
                    
                    if p_id not in valid_card_ids:
                        print(f"⚠️  ID SALTADO: Carta {p_id} en Lineup {lineup_id} NO EXISTE en user_cards. Saltando...")
                        skipped_ids.append((lineup_id, p_id))
                        continue
                    
                    # Insertar
                    conn.execute(
                        text("INSERT INTO gameweek_lineup_players (lineup_id, card_id) VALUES (:lid, :cid)"),
                        {"lid": lineup_id, "cid": p_id}
                    )
                    total_inserted += 1
            
            conn.commit()
            print(f"\n✅ Migración completada con éxito.")
            print(f"📊 Totales: {total_inserted} filas insertadas.")
            if skipped_ids:
                print(f"🚫 IDs saltados ({len(skipped_ids)}): {skipped_ids}")
            else:
                print("✨ No se saltó ningún ID.")

    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
