from sqlalchemy import create_engine, text

DATABASE_URL = "mysql+pymysql://root:@localhost:3306/ultimate_fantasy_legends"
engine = create_engine(DATABASE_URL)

def check_team_5():
    with engine.connect() as conn:
        print("--- Active Cards for Team 5 ---")
        q = """
        SELECT uc.id, p.name, p.position
        FROM user_cards uc
        JOIN players p ON p.id = uc.player_id
        WHERE uc.is_in_lineup = 1 AND uc.team_id = 5;
        """
        rows = conn.execute(text(q)).fetchall()
        print(f"Total: {len(rows)}")
        for r in rows:
            print(f"  ID {r[0]}: {r[1]} ({r[2]})")

if __name__ == "__main__":
    check_team_5()
