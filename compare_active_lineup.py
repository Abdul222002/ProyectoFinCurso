from sqlalchemy import create_engine, text

DATABASE_URL = "mysql+pymysql://root:@localhost:3306/ultimate_fantasy_legends"
engine = create_engine(DATABASE_URL)

def compare_lineups():
    with engine.connect() as conn:
        print("--- Comparativa Lineup 4 vs Live Lineup ---")
        
        # 1. Datos del Lineup 4 (CSV)
        q1 = "SELECT player_ids, active_formation FROM gameweek_lineups WHERE id = 4;"
        row1 = conn.execute(text(q1)).fetchone()
        print(f"\n[Lineup 4 (CSV)]: {row1[0]} (Formación: {row1[1]})") if row1 else print("Lineup 4 not found.")
        
        # 2. Datos Live (is_in_lineup=1)
        print("\n[Live Lineup (is_in_lineup=1)]:")
        q2 = """
        SELECT uc.id, p.name, p.position 
        FROM user_cards uc 
        JOIN players p ON p.id = uc.player_id 
        JOIN teams t ON t.id = uc.team_id 
        JOIN users u ON u.id = t.user_id 
        WHERE u.email = 'hakimbyaz@gmail.com' 
        AND uc.is_in_lineup = 1;
        """
        res2 = conn.execute(text(q2)).fetchall()
        live_ids = []
        for r in res2:
            print(f"  ID {r[0]}: {r[1]} ({r[2]})")
            live_ids.append(str(r[0]))
        
        print(f"\nPropuesta de ID CSV Live: '{','.join(live_ids)}'")

if __name__ == "__main__":
    compare_lineups()
