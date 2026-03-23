import pymysql
import sys

# Railway connection details
HOST = 'shinkansen.proxy.rlwy.net'
USER = 'root'
PASSWORD = 'WYlmwZNMvOmLiWjVUwgrsBgsqbTmdMtW'
PORT = 49059
DATABASE = 'railway'

FILE_PATH = 'ultimate_fantasy_legends_latest.sql'

def import_sql():
    print(f"Connecting to Railway MySQL at {HOST}:{PORT}...")
    try:
        conn = pymysql.connect(
            host=HOST, user=USER, password=PASSWORD, port=PORT, database=DATABASE,
            charset='utf8mb4', autocommit=True
        )
        
        with conn.cursor() as cursor:
            print(f"Reading {FILE_PATH}...")
            with open(FILE_PATH, 'r', encoding='utf-8-sig', errors='ignore') as f:
                lines = f.readlines()
            
            print("Processing and executing statements...")
            statement = ""
            for i, line in enumerate(lines):
                l = line.strip()
                if not l or l.startswith('--'):
                    continue
                
                # Keep /*! but ignore other /* comments
                if l.startswith('/*') and not l.startswith('/*!'):
                    continue
                
                statement += line
                if l.endswith(';'):
                    try:
                        cursor.execute(statement)
                    except Exception as e:
                        # Ignore "already exists" but log others
                        if "already exists" not in str(e).lower():
                            print(f"Error at line {i+1}: {e}")
                            # print(f"Statement: {statement[:100]}...")
                    statement = ""

        print("✅ Migration attempt finished!")
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import_sql()
