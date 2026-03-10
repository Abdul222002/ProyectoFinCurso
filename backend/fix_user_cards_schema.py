import os
from app.core.config import settings
from sqlalchemy import create_engine, text

def main():
    engine = create_engine(settings.database_url)
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE user_cards ADD COLUMN protected_value INT DEFAULT 0"))
            conn.commit()
            print("Successfully added protected_value column to user_cards")
    except Exception as e:
        print(f"Error executing ALTER TABLE: {e}")

if __name__ == "__main__":
    main()
