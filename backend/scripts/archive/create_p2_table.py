from sqlalchemy import create_engine, text

DATABASE_URL = "mysql+pymysql://root:@localhost:3306/ultimate_fantasy_legends"
engine = create_engine(DATABASE_URL)

sql = """
CREATE TABLE IF NOT EXISTS gameweek_lineup_players (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    lineup_id   INT NOT NULL,
    card_id     INT NOT NULL,
    position    VARCHAR(10) DEFAULT NULL,
    is_captain  TINYINT DEFAULT 0,
    FOREIGN KEY (lineup_id) REFERENCES gameweek_lineups(id) ON DELETE CASCADE,
    FOREIGN KEY (card_id)   REFERENCES user_cards(id)       ON DELETE CASCADE
);
"""

def create_table():
    try:
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
            print("✅ Table 'gameweek_lineup_players' created successfully.")
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        exit(1)

if __name__ == "__main__":
    create_table()
