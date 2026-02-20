import requests
import sys

BASE_URL = "http://localhost:8000"

def register(username, password):
    url = f"{BASE_URL}/auth/register"
    data = {"username": username, "email": f"{username}@example.com", "password": password}
    try:
        res = requests.post(url, json=data, timeout=5)
        if res.status_code == 201:
            print(f"Registered {username}")
        elif res.status_code == 400 and "already registered" in res.text:
            print(f"User {username} already exists")
        else:
            print(f"Failed to register {username}: {res.text}")
    except Exception as e:
        print(f"Error registering {username}: {e}")

def login(username, password):
    url = f"{BASE_URL}/auth/token"
    data = {"username": username, "password": password}
    try:
        res = requests.post(url, data=data, timeout=5)
        if res.status_code == 200:
            print(f"Logged in {username}")
            return res.json()["access_token"]
        else:
            print(f"Failed to login {username}: {res.text}")
            sys.exit(1)
    except Exception as e:
        print(f"Error logging in {username}: {e}")
        sys.exit(1)

def main():
    # 1. Setup Users
    u1 = "bidder1"
    u2 = "bidder2"
    register(u1, "password")
    register(u2, "password")
    
    t1 = login(u1, "password")
    t2 = login(u2, "password")
    
    headers1 = {"Authorization": f"Bearer {t1}"}
    headers2 = {"Authorization": f"Bearer {t2}"}

    # 2. Create League (User 1)
    print("\n--- Creating League ---")
    data = {"name": "AuctionTestLeague", "description": "Test", "max_members": 10, "is_public": True}
    res = requests.post(f"{BASE_URL}/leagues/", json=data, headers=headers1)
    if res.status_code == 201:
        league = res.json()
        lid = league["id"]
        invite_code = league["invite_code"]
        print(f"League created: ID={lid}, Code={invite_code}")
    else:
        # Try to find existing
        res = requests.get(f"{BASE_URL}/leagues/", headers=headers1)
        leagues = res.json()
        if leagues:
            league = leagues[0]
            lid = league["id"]
            invite_code = league["invite_code"]
            print(f"Using existing league: ID={lid}")
        else:
            print("Failed to create/find league")
            sys.exit(1)

    # 3. Join League (User 2)
    print("\n--- User 2 Joining ---")
    res = requests.post(f"{BASE_URL}/leagues/join/{invite_code}", headers=headers2)
    if res.status_code == 200:
        print("User 2 joined")
    elif res.status_code == 400:
        print("User 2 already in league")
    else:
        print(f"User 2 join failed: {res.text}")
        
    # 4. Check initial coins (User 1)
    print("\n--- Checking Coins ---")
    res = requests.get(f"{BASE_URL}/leagues/{lid}/members", headers=headers1)
    members = res.json()
    my_member = next((m for m in members if m["username"] == u1), None)
    if my_member:
        print(f"User 1 League Coins: {my_member['league_points']} (Wait, endpoint returns points not coins?)")
        # I didn't verify if member list returns coins... probably not.
        # But I can check via auction bid response or specific endpoint if I normalized it
        # Endpoints might need update to return coins in member list?
        # Let's trust the bid flow to show remaining coins.

    # 5. Get Auction
    print("\n--- Getting Auction ---")
    res = requests.get(f"{BASE_URL}/market/{lid}/auction", headers=headers1)
    if res.status_code != 200:
        print(f"Failed to get auction: {res.text}")
        sys.exit(1)
        
    auction = res.json()
    print(f"Auction active: {auction['is_active']}")
    print(f"Ends at: {auction['ends_at']}")
    slots = auction["slots"]
    print(f"Slots count: {len(slots)}")
    
    if len(slots) == 0:
        print("No slots found!")
        sys.exit(1)
        
    # Verify no legends
    legends = [s for s in slots if s["base_rarity"] == "legend"]
    if legends:
        print(f"ERROR: Found {len(legends)} legends in auction!")
    else:
        print("SUCCESS: No legends in auction.")
        
    target_slot = slots[0]
    sid = target_slot["id"]
    base_price = target_slot["base_price"]
    print(f"Target Slot: {target_slot['player_name']} (Base: {base_price})")
    
    # 6. Place Bid (User 1)
    print("\n--- User 1 Bidding ---")
    bid_amount = base_price
    print(f"Bidding {bid_amount}...")
    res = requests.post(f"{BASE_URL}/market/{lid}/bid/{sid}", json={"amount": bid_amount}, headers=headers1)
    if res.status_code == 200:
        data = res.json()
        print(f"Bid successful! New bid: {data['new_bid']}, Remaining Coins: {data['remaining_coins']}")
    else:
        print(f"Bid failed: {res.text}")
        
    # 7. User 2 Outbids
    print("\n--- User 2 Outbidding ---")
    bid_amount_2 = base_price + 2_000_000
    print(f"Bidding {bid_amount_2}...")
    res = requests.post(f"{BASE_URL}/market/{lid}/bid/{sid}", json={"amount": bid_amount_2}, headers=headers2)
    if res.status_code == 200:
        data = res.json()
        print(f"Bid successful! New bid: {data['new_bid']}, Remaining Coins: {data['remaining_coins']}")
    else:
        print(f"Bid failed: {res.text}")

    # 8. Verify Auction State
    print("\n--- Verifying Auction State ---")
    res = requests.get(f"{BASE_URL}/market/{lid}/auction", headers=headers1)
    auction = res.json()
    slot = next(s for s in auction["slots"] if s["id"] == sid)
    print(f"Slot {sid} Current Bid: {slot['current_bid']}")
    print(f"Highest Bidder: {slot['highest_bidder_username']}")
    
    if slot['highest_bidder_username'] == u2:
        print("SUCCESS: User 2 is highest bidder.")
    else:
        print("FAILURE: User 2 is NOT highest bidder.")

if __name__ == "__main__":
    main()
