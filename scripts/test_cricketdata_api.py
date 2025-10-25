#!/usr/bin/env python3
"""
CricketData.org API Shadow Testing Script
==========================================
Tests the cricket API WITHOUT integrating into the live app.
Runs completely independently - zero risk to production.

Usage:
    python test_cricketdata_api.py --match-id <id>
    python test_cricketdata_api.py --list-matches
    python test_cricketdata_api.py --test-match 1  (for ODI 1)
"""

import requests
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any
import time
import sys
import os

# API Configuration
API_KEY = "82fec341-b050-4b1c-9a9d-72359c591820"
BASE_URL = "https://api.cricapi.com"

# NZ vs England ODI Series Matches
MATCHES = {
    "1": {
        "date": "2025-10-26 14:00:00 UTC",
        "venue": "Bay Oval, Mount Maunganui",
        "name": "NZ vs ENG ODI 1"
    },
    "2": {
        "date": "2025-10-29 14:00:00 UTC",
        "venue": "Seddon Park, Hamilton",
        "name": "NZ vs ENG ODI 2"
    },
    "3": {
        "date": "2025-11-01 14:00:00 UTC",
        "venue": "Basin Reserve, Wellington",
        "name": "NZ vs ENG ODI 3"
    }
}

# Our player database mapping (externalId from seed script)
PLAYER_MAPPING = {
    # England Players
    "Harry Brook": "harry-brook",
    "Joe Root": "joe-root",
    "Ben Duckett": "ben-duckett",
    "Tom Banton": "tom-banton",
    "Sam Curran": "sam-curran",
    "Liam Dawson": "liam-dawson",
    "Jacob Bethell": "jacob-bethell",
    "Jamie Overton": "jamie-overton",
    "Jos Buttler": "jos-buttler",
    "Jamie Smith": "jamie-smith",
    "Jofra Archer": "jofra-archer",
    "Brydon Carse": "brydon-carse",
    "Adil Rashid": "adil-rashid",
    "Rehan Ahmed": "rehan-ahmed",
    "Luke Wood": "luke-wood",
    "Sonny Baker": "sonny-baker",
    
    # New Zealand Players
    "Kane Williamson": "kane-williamson",
    "Devon Conway": "devon-conway",
    "Will Young": "will-young",
    "Mitchell Santner": "mitchell-santner",
    "Michael Bracewell": "michael-bracewell",
    "Mark Chapman": "mark-chapman",
    "Daryl Mitchell": "daryl-mitchell",
    "Rachin Ravindra": "rachin-ravindra",
    "Tom Latham": "tom-latham",
    "Matt Henry": "matt-henry",
    "Kyle Jamieson": "kyle-jamieson",
    "Jacob Duffy": "jacob-duffy",
    "Zak Foulkes": "zak-foulkes",
    "Nathan Smith": "nathan-smith"
}


class CricketDataAPITester:
    """Shadow testing for CricketData.org API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = BASE_URL
        self.results = []
        self.artifacts_dir = "/app/artifacts"
        
        # Ensure artifacts directory exists
        os.makedirs(self.artifacts_dir, exist_ok=True)
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make API request with error handling"""
        url = f"{self.base_url}/{endpoint}"
        
        # Add API key to params
        if params is None:
            params = {}
        params['apikey'] = self.api_key
        
        print(f"\n🔍 API Request: {endpoint}")
        print(f"   URL: {url}")
        print(f"   Params: {params}")
        
        try:
            start_time = time.time()
            response = requests.get(url, params=params, timeout=10)
            elapsed = time.time() - start_time
            
            print(f"   ⏱️  Response time: {elapsed:.2f}s")
            print(f"   📊 Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success!")
                return data
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"   ❌ Timeout after 10 seconds")
            return None
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request error: {str(e)}")
            return None
        except Exception as e:
            print(f"   ❌ Unexpected error: {str(e)}")
            return None
    
    def test_api_connectivity(self) -> bool:
        """Test basic API connectivity"""
        print("\n" + "="*60)
        print("🔌 TESTING API CONNECTIVITY")
        print("="*60)
        
        # Try current matches endpoint
        data = self._make_request("v1/currentMatches", {"offset": 0})
        
        if data:
            print("\n✅ API is accessible!")
            return True
        else:
            print("\n❌ API connection failed!")
            return False
    
    def list_current_matches(self) -> List[Dict]:
        """List all currently available matches"""
        print("\n" + "="*60)
        print("📋 LISTING CURRENT MATCHES")
        print("="*60)
        
        data = self._make_request("v1/current_matches")
        
        if data and 'data' in data:
            matches = data['data']
            print(f"\n   Found {len(matches)} matches")
            
            for i, match in enumerate(matches[:10], 1):  # Show first 10
                print(f"\n   {i}. {match.get('name', 'Unknown')}")
                print(f"      ID: {match.get('id')}")
                print(f"      Status: {match.get('status')}")
                print(f"      Teams: {match.get('teamA')} vs {match.get('teamB')}")
            
            return matches
        else:
            print("\n   ❌ No matches found")
            return []
    
    def find_nz_england_match(self) -> Optional[str]:
        """Try to find NZ vs England ODI match ID"""
        print("\n" + "="*60)
        print("🔍 SEARCHING FOR NZ vs ENGLAND MATCH")
        print("="*60)
        
        matches = self.list_current_matches()
        
        for match in matches:
            name = match.get('name', '').lower()
            teamA = match.get('teamA', '').lower()
            teamB = match.get('teamB', '').lower()
            
            # Look for New Zealand and England
            if ('new zealand' in name or 'england' in name or 
                'new zealand' in teamA or 'england' in teamA or
                'new zealand' in teamB or 'england' in teamB):
                
                print(f"\n   ✅ FOUND POTENTIAL MATCH:")
                print(f"      ID: {match.get('id')}")
                print(f"      Name: {match.get('name')}")
                print(f"      Teams: {match.get('teamA')} vs {match.get('teamB')}")
                
                return match.get('id')
        
        print("\n   ❌ NZ vs England match not found in current matches")
        return None
    
    def get_match_scorecard(self, match_id: str) -> Optional[Dict]:
        """Fetch detailed match scorecard"""
        print("\n" + "="*60)
        print(f"📊 FETCHING MATCH SCORECARD: {match_id}")
        print("="*60)
        
        data = self._make_request(f"v1/match_scorecard", {"match_id": match_id})
        
        if data:
            self._save_snapshot(data, f"scorecard_{match_id}")
            self._analyze_scorecard(data)
            return data
        
        return None
    
    def _analyze_scorecard(self, data: Dict):
        """Analyze scorecard structure"""
        print("\n" + "="*60)
        print("🔬 SCORECARD ANALYSIS")
        print("="*60)
        
        print(f"\n📌 Top-level keys: {list(data.keys())}")
        
        # Try to find player stats
        if 'data' in data:
            match_data = data['data']
            print(f"\n📌 Match data keys: {list(match_data.keys())}")
            
            # Look for player stats
            if 'players' in match_data:
                players = match_data['players']
                print(f"\n👥 Found {len(players)} players")
                
                if players:
                    sample = players[0]
                    print(f"\n📌 Sample player structure:")
                    print(json.dumps(sample, indent=2)[:500])
            
            # Look for innings data
            if 'innings' in match_data:
                innings = match_data['innings']
                print(f"\n🏏 Found {len(innings)} innings")
    
    def _save_snapshot(self, data: Dict, name: str):
        """Save API response snapshot"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.artifacts_dir}/api_{name}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n💾 Saved snapshot: {filename}")
    
    def test_player_mapping(self, api_players: List[Dict]):
        """Test if API players map to our database"""
        print("\n" + "="*60)
        print("🔗 TESTING PLAYER MAPPING")
        print("="*60)
        
        mapped = 0
        unmapped = []
        
        for player in api_players:
            name = player.get('name', player.get('player_name', 'Unknown'))
            
            if name in PLAYER_MAPPING:
                our_id = PLAYER_MAPPING[name]
                print(f"   ✅ {name} → {our_id}")
                mapped += 1
            else:
                print(f"   ❌ {name} → NO MATCH")
                unmapped.append(name)
        
        print(f"\n📊 Mapping Summary:")
        print(f"   Total players: {len(api_players)}")
        print(f"   Mapped: {mapped}")
        print(f"   Unmapped: {len(unmapped)}")
        print(f"   Success rate: {(mapped/len(api_players)*100):.1f}%")
        
        if unmapped:
            print(f"\n⚠️  Unmapped players:")
            for name in unmapped:
                print(f"      - {name}")
    
    def convert_to_csv_format(self, scorecard: Dict) -> List[Dict]:
        """Attempt to convert API data to our CSV format"""
        print("\n" + "="*60)
        print("🔄 TESTING CSV CONVERSION")
        print("="*60)
        
        csv_rows = []
        
        print("\n⚠️  Note: Actual conversion logic depends on API response structure")
        print("   This will be implemented after analyzing real match data")
        
        # Placeholder for conversion logic
        # Will be implemented after seeing actual API response
        
        return csv_rows
    
    def run_live_monitoring(self, match_id: str, interval: int = 300):
        """Monitor match in real-time (every 5 minutes by default)"""
        print("\n" + "="*60)
        print(f"🔴 STARTING LIVE MONITORING: {match_id}")
        print(f"   Interval: {interval} seconds ({interval/60:.0f} minutes)")
        print("   Press Ctrl+C to stop")
        print("="*60)
        
        iteration = 1
        
        try:
            while True:
                print(f"\n\n{'='*60}")
                print(f"📊 ITERATION {iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print('='*60)
                
                scorecard = self.get_match_scorecard(match_id)
                
                if scorecard:
                    print(f"\n✅ Data fetched successfully")
                else:
                    print(f"\n❌ Failed to fetch data")
                
                print(f"\n⏰ Next update in {interval} seconds...")
                time.sleep(interval)
                
                iteration += 1
                
        except KeyboardInterrupt:
            print(f"\n\n⏹️  Monitoring stopped after {iteration} iterations")
            print(f"💾 All data saved to: {self.artifacts_dir}")
    
    def generate_report(self, match_number: str):
        """Generate test report"""
        print("\n" + "="*60)
        print(f"📝 GENERATING TEST REPORT FOR ODI {match_number}")
        print("="*60)
        
        report_path = f"{self.artifacts_dir}/test_report_odi{match_number}.md"
        
        report = f"""# Cricket API Shadow Test Report - ODI {match_number}

## Match Details
- **Match**: {MATCHES[match_number]['name']}
- **Date**: {MATCHES[match_number]['date']}
- **Venue**: {MATCHES[match_number]['venue']}
- **Test Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Test Results

### API Connectivity
- [ ] API accessible
- [ ] Authentication working
- [ ] Response times acceptable (<5s)

### Match Data
- [ ] Match found in current_matches
- [ ] Match ID identified
- [ ] Scorecard accessible
- [ ] Live data updating

### Player Data
- [ ] All 30 players present
- [ ] Player mapping successful (% mapped: ___)
- [ ] Statistics complete (runs, wickets, catches, stumpings, run-outs)

### Data Quality
- [ ] Accuracy vs official scorecard: ____%
- [ ] Stumpings tracked: Yes/No
- [ ] Run-outs tracked: Yes/No
- [ ] Data delay: ___ minutes

### Technical Issues
- [ ] No API downtime
- [ ] No rate limiting
- [ ] No authentication errors

## Findings

### What Worked Well
- 

### Issues Discovered
- 

### Missing Data
- 

## Recommendation

- [ ] ✅ GO - Ready for ODI {int(match_number) + 1}
- [ ] 🟡 MODIFY - Needs adjustments
- [ ] ❌ NO-GO - Stick with manual CSV

## Notes

"""
        
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"\n📄 Report template saved: {report_path}")
        print(f"   Fill in results after testing")


def main():
    parser = argparse.ArgumentParser(description='Shadow test CricketData API')
    parser.add_argument('--list-matches', action='store_true', 
                       help='List all current matches')
    parser.add_argument('--find-match', action='store_true',
                       help='Find NZ vs England match ID')
    parser.add_argument('--match-id', type=str,
                       help='Test specific match ID')
    parser.add_argument('--test-match', type=str, choices=['1', '2', '3'],
                       help='Test ODI match (1, 2, or 3)')
    parser.add_argument('--monitor', action='store_true',
                       help='Start live monitoring (5 min intervals)')
    parser.add_argument('--interval', type=int, default=300,
                       help='Monitoring interval in seconds (default: 300)')
    parser.add_argument('--connectivity', action='store_true',
                       help='Test API connectivity only')
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = CricketDataAPITester(API_KEY)
    
    print("\n" + "="*60)
    print("🏏 CRICKETDATA.ORG API SHADOW TESTER")
    print("   NZ vs England ODI Series 2025")
    print("="*60)
    
    # Test connectivity first
    if not tester.test_api_connectivity():
        print("\n❌ Cannot proceed - API not accessible")
        return 1
    
    # Execute requested action
    if args.list_matches:
        tester.list_current_matches()
    
    elif args.find_match:
        match_id = tester.find_nz_england_match()
        if match_id:
            print(f"\n✅ Use this match ID: {match_id}")
        else:
            print(f"\n❌ Match not found - may not be started yet")
    
    elif args.match_id:
        scorecard = tester.get_match_scorecard(args.match_id)
        
        if scorecard and args.monitor:
            tester.run_live_monitoring(args.match_id, args.interval)
    
    elif args.test_match:
        match_num = args.test_match
        print(f"\n📋 Testing ODI {match_num}")
        print(f"   {MATCHES[match_num]['name']}")
        print(f"   {MATCHES[match_num]['date']}")
        print(f"   {MATCHES[match_num]['venue']}")
        
        # Try to find match
        match_id = tester.find_nz_england_match()
        
        if match_id:
            scorecard = tester.get_match_scorecard(match_id)
            
            if scorecard and args.monitor:
                tester.run_live_monitoring(match_id, args.interval)
        else:
            print(f"\n⚠️  Match not found yet")
            print(f"   Try again when match is live")
        
        # Generate report template
        tester.generate_report(match_num)
    
    elif args.connectivity:
        # Already tested connectivity above
        pass
    
    else:
        parser.print_help()
    
    print("\n✅ Shadow testing complete!")
    print(f"📁 Artifacts saved to: {tester.artifacts_dir}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
