"""
Script to create a test user with email user@user.com and password 123456
"""
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.models import User, UserRole
from app.routers.auth import hash_password
from datetime import datetime

def create_test_user():
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing = db.query(User).filter(User.email == 'user@user.com').first()
        if existing:
            print(f"❌ User with email 'user@user.com' already exists!")
            print(f"   ID: {existing.id}")
            print(f"   Username: {existing.username}")
            print(f"   Email verified: {existing.email_verified}")
            return
        
        # Create the user
        new_user = User(
            username='usuario_prueba',
            email='user@user.com',
            password_hash=hash_password('123456'),
            role=UserRole.FREE,
            email_verified=True,  # Set to True for testing
            global_elo=1000,
            arena_tickets=5,
            last_tickets_reset=datetime.utcnow(),
            arena_wins=0,
            arena_losses=0,
            arena_draws=0,
            total_points=0,
            level=1,
            experience=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print("✅ Test user created successfully!")
        print(f"   ID: {new_user.id}")
        print(f"   Username: {new_user.username}")
        print(f"   Email: {new_user.email}")
        print(f"   Role: {new_user.role.value}")
        print(f"   Email verified: {new_user.email_verified}")
        print(f"\n🔑 Login credentials:")
        print(f"   Email: user@user.com")
        print(f"   Password: 123456")
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
