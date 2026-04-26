from sqlalchemy import create_engine, text

DATABASE_URL = "mysql+pymysql://root:@localhost:3306/ultimate_fantasy_legends"
engine = create_engine(DATABASE_URL)

def diagnose_active():
    with engine.connect() as conn:
        print("--- Diagnóstico: 22 Cartas Activas para hakimbyaz@gmail.com ---")
        q = """
        SELECT uc.id, p.name, p.position, uc.team_id, t.name as team_name
        FROM user_cards uc
        JOIN players p ON p.id = uc.player_id
        JOIN teams t ON t.id = uc.team_id
        WHERE uc.is_in_lineup = 1
        AND uc.user_id = (SELECT id FROM users WHERE email = 'hakimbyaz@gmail.com')
        ORDER BY uc.team_id, uc.id;
        """
        rows = conn.execute(text(q)).fetchall()
        print(f"Total de cartas marcadas con is_in_lineup = 1: {len(rows)}")
        
        for r in rows:
            print(f"ID: {r[0]} | Jugador: {r[1]} ({r[2]}) | TeamID: {r[3]} ({r[4]})")

if __name__ == "__main__":
    diagnose_active()
