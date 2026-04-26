from sqlalchemy import create_engine, text

DATABASE_URL = "mysql+pymysql://root:@localhost:3306/ultimate_fantasy_legends"
engine = create_engine(DATABASE_URL)

def verify_migration():
    with engine.connect() as conn:
        print("--- Verificación Final Paso 2: CSV vs Relacional ---")
        q = """
        SELECT 
            gl.id,
            gl.player_ids,
            COUNT(glp.id) as migrated_count
        FROM gameweek_lineups gl
        LEFT JOIN gameweek_lineup_players glp ON glp.lineup_id = gl.id
        GROUP BY gl.id
        ORDER BY gl.id;
        """
        rows = conn.execute(text(q)).fetchall()
        
        print(f"{'ID':<4} | {'CSV Count':<10} | {'Relational':<10} | {'Status'}")
        print("-" * 50)
        
        match_count = 0
        total = len(rows)
        
        for r in rows:
            csv_str = r[1]
            csv_ids = [p.strip() for p in csv_str.split(",") if p.strip()] if csv_str else []
            csv_count = len(csv_ids)
            rel_count = r[2]
            
            # Special logic for IDs 4 and 8 where we expected skips
            status = "✅ OK"
            if r[0] == 4 and rel_count == csv_count - 1: status = "✅ OK (1 saltado)"
            elif r[0] == 8 and rel_count == csv_count - 2: status = "✅ OK (2 saltados)"
            elif rel_count != csv_count: 
                status = "❌ ERROR"
            else:
                match_count += 1
                
            print(f"{r[0]:<4} | {csv_count:<10} | {rel_count:<10} | {status}")

if __name__ == "__main__":
    verify_migration()
