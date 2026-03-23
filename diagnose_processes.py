from sqlalchemy import create_engine, text

DATABASE_URL = "mysql+pymysql://root:@localhost:3306/ultimate_fantasy_legends"
engine = create_engine(DATABASE_URL)

def run_diagnostics():
    with engine.connect() as conn:
        print("--- Procesos MySQL ---")
        procs = conn.execute(text("SHOW PROCESSLIST")).fetchall()
        for p in procs:
            print(p)
            
        print("\n--- Diagnóstico Hakim (Teams & Active Cards) ---")
        q = """
        SELECT t.id, t.name, t.league_id, COUNT(uc.id) as cartas_activas
        FROM teams t
        JOIN user_cards uc ON uc.team_id = t.id AND uc.is_in_lineup = 1
        JOIN users u ON u.id = t.user_id
        WHERE u.email = 'hakimbyaz@gmail.com'
        GROUP BY t.id;
        """
        rows = conn.execute(text(q)).fetchall()
        for r in rows:
            print(f"Team ID: {r[0]} | Team Name: {r[1]} | League ID: {r[2]} | Active Cards: {r[3]}")

if __name__ == "__main__":
    run_diagnostics()
