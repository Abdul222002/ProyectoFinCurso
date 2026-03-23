from sqlalchemy import create_engine, text

DATABASE_URL = "mysql+pymysql://root:@localhost:3306/ultimate_fantasy_legends"
engine = create_engine(DATABASE_URL)

def debug_lineup():
    with engine.connect() as conn:
        row = conn.execute(text("SELECT id, team_id, gameweek_id, player_ids FROM gameweek_lineups WHERE id = 4")).fetchone()
        if row:
            print(f"Lineup ID: {row[0]}")
            print(f"Team ID: {row[1]}")
            print(f"GW ID: {row[2]}")
            print(f"Player IDs (CSV): '{row[3]}'")
            
            p_ids = [p.strip() for p in row[3].split(",") if p.strip()]
            for pid in p_ids:
                exists = conn.execute(text(f"SELECT id FROM user_cards WHERE id = {pid}")).fetchone()
                if exists:
                    print(f"  Mapping ID {pid}: ✅ OK")
                else:
                    print(f"  Mapping ID {pid}: ❌ MISSING in user_cards")
        else:
            print("Lineup 4 not found.")

if __name__ == "__main__":
    debug_lineup()
