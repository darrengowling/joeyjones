#!/usr/bin/env python3
"""
Manual Migration Runner
Use this to run the migration directly against production
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, '/app/backend')

# Load environment variables
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

print("\n" + "="*80)
print("MANUAL MIGRATION RUNNER")
print("="*80)
print(f"\nThis will update team names in the database:")
print(f"  Database: {os.environ.get('DB_NAME', 'not set')}")

mongo_url = os.environ.get('MONGO_URL', '')
if 'localhost' in mongo_url:
    print(f"  Environment: LOCAL (localhost)")
elif 'mongodb.net' in mongo_url or 'atlas' in mongo_url.lower():
    print(f"  Environment: PRODUCTION (MongoDB Atlas)")
else:
    print(f"  Environment: Unknown")

response = input("\n⚠️  Continue with migration? (yes/no): ")
if response.lower() != 'yes':
    print("\n❌ Migration cancelled")
    sys.exit(0)

print("\n🚀 Starting migration...\n")

# Import and run migration
from migrate_team_names_v2 import migrate_team_names

async def main():
    success = await migrate_team_names()
    return success

success = asyncio.run(main())

if success:
    print("\n" + "="*80)
    print("✅ MIGRATION COMPLETED SUCCESSFULLY")
    print("="*80)
    print("\nNext steps:")
    print("1. Test scoring in your production leagues")
    print("2. Verify points are being calculated correctly")
    print("="*80)
    sys.exit(0)
else:
    print("\n" + "="*80)
    print("❌ MIGRATION FAILED")
    print("="*80)
    print("\nPlease check the error messages above")
    sys.exit(1)
