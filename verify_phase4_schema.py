from sqlalchemy import create_engine, text

DATABASE_URL = "mysql+pymysql://root:@localhost:3306/ultimate_fantasy_legends"
engine = create_engine(DATABASE_URL)

def verify_phase4():
    with engine.connect() as conn:
        print("--- Verificando Vista player_stats_summary ---")
        try:
            res = conn.execute(text("DESC player_stats_summary")).fetchall()
            for row in res:
                print(row)
        except Exception as e:
            print(f"❌ Error al ver la vista: {e}")

        print("\n--- Verificando Constraint chk_winner en arena_battles ---")
        try:
            # En MySQL 8.0, los CHECK constraints están en CHECK_CONSTRAINTS
            q = "SELECT * FROM information_schema.CHECK_CONSTRAINTS WHERE CONSTRAINT_NAME = 'chk_winner'"
            res = conn.execute(text(q)).fetchall()
            if res:
                for row in res:
                    print(row)
            else:
                print("⚠️ Constraint 'chk_winner' no encontrado en CHECK_CONSTRAINTS. Probablemente MySQL version < 8.0 o MariaDB.")
                # Intentar en TABLE_CONSTRAINTS por si acaso
                q2 = "SELECT * FROM information_schema.TABLE_CONSTRAINTS WHERE TABLE_NAME = 'arena_battles' AND CONSTRAINT_NAME = 'chk_winner'"
                res2 = conn.execute(text(q2)).fetchall()
                for row in res2:
                    print(row)
        except Exception as e:
            print(f"❌ Error al ver constraints: {e}")

        print("\n--- Comparando Datos: Players (Columnas) vs View ---")
        q_comp = """
        SELECT 
            p.id,
            p.total_matches_played  AS col_matches,
            s.total_matches_played  AS view_matches,
            p.sum_fantasy_points    AS col_points,
            s.sum_fantasy_points    AS view_points
        FROM players p
        JOIN player_stats_summary s ON s.player_id = p.id
        WHERE p.total_matches_played != s.total_matches_played
           OR ABS(p.sum_fantasy_points - s.sum_fantasy_points) > 0.01
        LIMIT 20;
        """
        diffs = conn.execute(text(q_comp)).fetchall()
        if not diffs:
            print("✅ ¡ÉXITO! Los datos coinciden al 100%. Cero diferencias encontradas.")
        else:
            print(f"⚠️ Se encontraron {len(diffs)} diferencias:")
            for d in diffs:
                print(d)

if __name__ == "__main__":
    verify_phase4()
