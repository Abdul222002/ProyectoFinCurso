"""
Generate System Offers — Run daily via scheduler

Checks market listings older than 24h with no buyer.
Creates a SystemOffer at 80-95% of the asking price.
Offers expire after 48h.
"""

import sys
import os
import random
from datetime import datetime, timedelta

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.models import MarketListing, SystemOffer


def generate_offers():
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=24)

        # Find listings older than 24h that haven't received an offer yet
        listings = db.query(MarketListing).filter(
            MarketListing.is_active == True,
            MarketListing.listed_at < cutoff
        ).all()

        created = 0
        for listing in listings:
            # Check if already has an active offer
            existing_offer = db.query(SystemOffer).filter(
                SystemOffer.listing_id == listing.id,
                SystemOffer.is_expired == False,
                SystemOffer.is_accepted == False
            ).first()

            if existing_offer:
                continue

            # Generate offer at 80-95% of asking price
            discount = random.uniform(0.80, 0.95)
            offer_price = int(listing.asking_price * discount)

            offer = SystemOffer(
                listing_id=listing.id,
                card_id=listing.card_id,
                user_id=listing.seller_id,
                league_id=listing.league_id,
                offer_price=offer_price,
                offered_at=now,
                expires_at=now + timedelta(hours=48)
            )
            db.add(offer)
            created += 1
            print(f"  Oferta creada: Listing #{listing.id} → {offer_price:,} ({discount:.0%} de {listing.asking_price:,})")

        db.commit()
        print(f"\n✅ {created} ofertas del sistema generadas")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🤖 Generando ofertas del sistema...")
    generate_offers()
