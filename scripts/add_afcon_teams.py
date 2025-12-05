#!/usr/bin/env python3
"""
Add 24 AFCON 2025/26 teams to the database
"""
import sys
sys.path.insert(0, '/app/backend')

from pymongo import MongoClient
import os
from datetime import datetime, timezone
from uuid import uuid4

# Load environment
mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/')
db_name = os.getenv('DB_NAME', 'test_database')

# Connect to database
client = MongoClient(mongo_url)
db = client[db_name]

# 24 AFCON Teams (English names, organized by group)
AFCON_TEAMS = [
    # Group A
    {"name": "Morocco", "country": "Morocco"},
    {"name": "Mali", "country": "Mali"},
    {"name": "Zambia", "country": "Zambia"},
    {"name": "Comoros", "country": "Comoros"},
    
    # Group B
    {"name": "Egypt", "country": "Egypt"},
    {"name": "South Africa", "country": "South Africa"},
    {"name": "Angola", "country": "Angola"},
    {"name": "Zimbabwe", "country": "Zimbabwe"},
    
    # Group C
    {"name": "Nigeria", "country": "Nigeria"},
    {"name": "Tunisia", "country": "Tunisia"},
    {"name": "Uganda", "country": "Uganda"},
    {"name": "Tanzania", "country": "Tanzania"},
    
    # Group D
    {"name": "Senegal", "country": "Senegal"},
    {"name": "DR Congo", "country": "Democratic Republic of Congo"},
    {"name": "Benin", "country": "Benin"},
    {"name": "Botswana", "country": "Botswana"},
    
    # Group E
    {"name": "Algeria", "country": "Algeria"},
    {"name": "Burkina Faso", "country": "Burkina Faso"},
    {"name": "Equatorial Guinea", "country": "Equatorial Guinea"},
    {"name": "Sudan", "country": "Sudan"},
    
    # Group F
    {"name": "Ivory Coast", "country": "Ivory Coast"},
    {"name": "Cameroon", "country": "Cameroon"},
    {"name": "Gabon", "country": "Gabon"},
    {"name": "Mozambique", "country": "Mozambique"},
]

def add_afcon_teams():
    """Add all 24 AFCON teams to the database"""
    
    print("=" * 70)
    print("ADDING AFCON 2025/26 TEAMS")
    print("=" * 70)
    
    # Check for existing AFCON teams
    existing_count = db.assets.count_documents({'competitionShort': 'AFCON'})
    if existing_count > 0:
        print(f"\n⚠️  Warning: {existing_count} AFCON teams already exist")
        response = input("Continue and add more? (y/n): ")
        if response.lower() != 'y':
            print("Aborted")
            return
    
    now = datetime.now(timezone.utc).isoformat()
    added_count = 0
    skipped_count = 0
    
    print(f"\nAdding {len(AFCON_TEAMS)} teams...\n")
    
    for i, team_data in enumerate(AFCON_TEAMS, 1):
        team_name = team_data["name"]
        
        # Check if team already exists
        existing = db.assets.find_one({
            'name': team_name,
            'sportKey': 'football',
            'competitionShort': 'AFCON'
        })
        
        if existing:
            print(f"  ⏭️  {i:2d}. {team_name:<25} - Already exists")
            skipped_count += 1
            continue
        
        # Create team document
        team_doc = {
            "id": str(uuid4()),
            "sportKey": "football",
            "name": team_name,
            "externalId": f"AFCON_{i:03d}",  # AFCON_001 to AFCON_024
            "city": "",
            "selected": True,
            "createdAt": now,
            "updatedAt": now,
            "apiFootballId": "",
            "competition": "Africa Cup of Nations",
            "competitionShort": "AFCON",
            "country": team_data["country"],
            "logo": None,
            "uefaId": "",
            "competitions": ["Africa Cup of Nations"]
        }
        
        # Insert into database
        db.assets.insert_one(team_doc)
        print(f"  ✅ {i:2d}. {team_name:<25} (ID: AFCON_{i:03d})")
        added_count += 1
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Added: {added_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Total AFCON teams in database: {db.assets.count_documents({'competitionShort': 'AFCON'})}")
    print("=" * 70)
    
    if added_count > 0:
        print("\n✅ AFCON teams successfully added to database!")
    else:
        print("\n⚠️  No new teams added")

if __name__ == "__main__":
    add_afcon_teams()
