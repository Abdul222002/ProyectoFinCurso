import pymysql
import sys

# Railway connection details
HOST = 'shinkansen.proxy.rlwy.net'
USER = 'root'
PASSWORD = 'WYlmwZNMvOmLiWjVUwgrsBgsqbTmdMtW'
PORT = 49059
DATABASE = 'railway'

def verify():
    try:
        conn = pymysql.connect(
            host=HOST, user=USER, password=PASSWORD, port=PORT, database=DATABASE, charset='utf8mb4'
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username FROM users")
            users = cursor.fetchall()
            print(f"Users in Railway: {users}")
            
            cursor.execute("SELECT id, name FROM leagues")
            leagues = cursor.fetchall()
            print(f"Leagues in Railway: {leagues}")
            
            cursor.execute("SELECT COUNT(*) FROM players")
            count = cursor.fetchone()[0]
            print(f"Players count: {count}")

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify()
