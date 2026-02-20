from app.core.database import engine, Base
from sqlalchemy import text
from app.models.models import MarketAuction, AuctionSlot, AuctionBid

def update_schema():
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Add coins to league_members
            print("Adding coins to league_members...")
            try:
                conn.execute(text("ALTER TABLE league_members ADD COLUMN coins INTEGER DEFAULT 100000000"))
            except Exception as e:
                print(f"Error adding coins (maybe exists): {e}")

            # 2. Add league_id to user_cards
            print("Adding league_id to user_cards...")
            try:
                conn.execute(text("ALTER TABLE user_cards ADD COLUMN league_id INTEGER REFERENCES leagues(id)"))
            except Exception as e:
                print(f"Error adding league_id (maybe exists): {e}")

            trans.commit()
            print("Columns added.")
        except Exception as e:
            trans.rollback()
            print(f"Transaction failed: {e}")

    # 3. Create new tables
    print("Creating new tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

if __name__ == "__main__":
    update_schema()
