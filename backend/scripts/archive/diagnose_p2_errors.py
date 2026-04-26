from sqlalchemy import create_engine, text

DATABASE_URL = "mysql+pymysql://root:@localhost:3306/ultimate_fantasy_legends"
engine = create_engine(DATABASE_URL)

def run_diagnostics():
    with engine.connect() as conn:
        print("--- Diagnóstico Lineups 4 y 8 ---")
        
        # 1. Gameweeks
        print("\n1. Gameweeks Info:")
        q1 = """
        SELECT gl.id, gl.gameweek_id, gl.player_ids, gw.number, gw.is_finished
        FROM gameweek_lineups gl
        JOIN gameweeks gw ON gw.id = gl.gameweek_id
        WHERE gl.id IN (4, 8);
        """
        res1 = conn.execute(text(q1)).fetchall()
        for r in res1: print(r)
        
        # 2. Points
        print("\n2. Points Earned:")
        q2 = "SELECT id, points_earned FROM gameweek_lineups WHERE id IN (4, 8);"
        res2 = conn.execute(text(q2)).fetchall()
        for r in res2: print(r)
        
        # 3. User/Team
        print("\n3. User/Team Info:")
        q3 = """
        SELECT gl.id, t.name as team_name, u.username
        FROM gameweek_lineups gl
        JOIN teams t ON t.id = gl.team_id
        JOIN users u ON u.id = t.user_id
        WHERE gl.id IN (4, 8);
        """
        res3 = conn.execute(text(q3)).fetchall()
        for r in res3: print(r)

if __name__ == "__main__":
    run_diagnostics()
