from sqlalchemy import create_engine, text

DATABASE_URL = "mysql+pymysql://root:@localhost:3306/ultimate_fantasy_legends"
engine = create_engine(DATABASE_URL)

def scan_all():
    with engine.connect() as conn:
        valid_cards = {row[0] for row in conn.execute(text("SELECT id FROM user_cards")).fetchall()}
        lineups = conn.execute(text("SELECT id, player_ids FROM gameweek_lineups")).fetchall()
        
        missing_report = []
        
        for lid, p_str in lineups:
            if not p_str or p_str.strip() == "": continue
            ids = [p.strip() for p in p_str.split(",") if p.strip()]
            for pid in ids:
                if int(pid) not in valid_cards:
                    missing_report.append((lid, pid))
        
        if missing_report:
            print(f"Total missing references found: {len(missing_report)}")
            for lid, pid in missing_report:
                print(f"Lineup {lid} references missing Card {pid}")
        else:
            print("No more missing references found.")

if __name__ == "__main__":
    scan_all()
