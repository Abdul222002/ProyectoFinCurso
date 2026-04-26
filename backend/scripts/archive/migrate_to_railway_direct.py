import pymysql
import sys

# Local connection details
L_HOST = 'localhost'
L_USER = 'root'
L_PASSWORD = ''
L_DATABASE = 'ultimate_fantasy_legends'

# Railway connection details
R_HOST = 'shinkansen.proxy.rlwy.net'
R_USER = 'root'
R_PASSWORD = 'WYlmwZNMvOmLiWjVUwgrsBgsqbTmdMtW'
R_PORT = 49059
R_DATABASE = 'railway'

TABLES = [
    'users', 'leagues', 'league_members', 'teams', 'players', 
    'user_cards', 'market_listings', 'market_auctions', 'auction_slots',
    'auction_bids', 'arena_battles', 'pack_openings', 'gameweeks',
    'gameweek_lineups', 'matches', 'player_match_stats', 'system_offers'
]

def migrate():
    try:
        print("Connecting to local database...")
        l_conn = pymysql.connect(host=L_HOST, user=L_USER, password=L_PASSWORD, database=L_DATABASE, charset='utf8mb4')
        
        print(f"Connecting to Railway MySQL at {R_HOST}:{R_PORT}...")
        r_conn = pymysql.connect(
            host=R_HOST, user=R_USER, password=R_PASSWORD, port=R_PORT, database=R_DATABASE, 
            charset='utf8mb4', autocommit=True
        )

        with l_conn.cursor() as l_cursor, r_conn.cursor() as r_cursor:
            # Disable foreign key checks on remote
            r_cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            for table in TABLES:
                print(f"Migrating table: {table}...")
                
                # Fetch data from local
                l_cursor.execute(f"SELECT * FROM `{table}`")
                columns = [i[0] for i in l_cursor.description]
                rows = l_cursor.fetchall()
                
                if not rows:
                    print(f"  (Table {table} is empty localy, skipping copy)")
                    continue

                # Truncate remote table
                r_cursor.execute(f"TRUNCATE TABLE `{table}`")
                
                # Prepare insert statement
                placeholders = ", ".join(["%s"] * len(columns))
                col_names = ", ".join([f"`{c}`" for c in columns])
                sql = f"INSERT INTO `{table}` ({col_names}) VALUES ({placeholders})"
                
                # Execute in batches if many rows
                r_cursor.executemany(sql, rows)
                print(f"  Done! {len(rows)} rows copied.")

            # Re-enable foreign key checks
            r_cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        l_conn.close()
        r_conn.close()
        print("Migration complete!")

    except Exception as e:
        print(f"Error during migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
