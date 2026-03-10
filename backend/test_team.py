import sys
import os
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import Team, User
from app.routers.teams import _team_to_response
from app.schemas.team import TeamResponse
from pydantic import ValidationError

def main():
    db = SessionLocal()
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        print("User admin not found")
        # Try another user
        user = db.query(User).first()
        if not user:
            print("No users in DB")
            return
            
    print(f"Testing teams for user {user.username}")
    teams = db.query(Team).filter(Team.user_id == user.id).all()
    if not teams:
        print("No teams for user")
        
    for team in teams:
        print(f"\nProcessing team {team.name} (leauge {team.league_id})")
        try:
            resp_dict = _team_to_response(team)
            print("Successfully created dict from team")
            
            try:
                # Try validating through Pydantic to see if it strips anything or fails
                validated = TeamResponse(**resp_dict)
                print("Successfully validated with Pydantic!")
                # Let's see what is actually in the first player
                if validated.players:
                    print("First validated player fields:", validated.players[0].model_dump().keys())
                else:
                    print("No players in team")
            except ValidationError as e:
                print("Pydantic validation error:", e)
                
        except Exception as e:
            print(f"Error in _team_to_response: {e}")

if __name__ == "__main__":
    main()
