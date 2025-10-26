#!/root/.venv/bin/python3
"""
ESPNcricinfo Scorecard Scraper
================================
Scrapes live cricket scorecard data from ESPNcricinfo.
Extracts player statistics for fantasy scoring.

Usage:
    python scrape_espncricinfo.py --match-id 1491720
    python scrape_espncricinfo.py --match-id 1491720 --monitor --interval 600
"""

import requests
from bs4 import BeautifulSoup
import json
import argparse
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

# Match configurations
MATCHES = {
    "1": {
        "match_id": "1491720",
        "name": "NZ vs ENG ODI 1",
        "date": "2025-10-26"
    },
    "2": {
        "match_id": "1491721",
        "name": "NZ vs ENG ODI 2",
        "date": "2025-10-29"
    },
    "3": {
        "match_id": "1491722",
        "name": "NZ vs ENG ODI 3",
        "date": "2025-11-01"
    }
}

BASE_URL = "https://www.espn.com/cricket/series/23730/scorecard"

class ESPNCricinfoScraper:
    """Scraper for ESPNcricinfo scorecards"""
    
    def __init__(self, match_id: str):
        self.match_id = match_id
        self.artifacts_dir = "/app/artifacts"
        os.makedirs(self.artifacts_dir, exist_ok=True)
        
        # User agent to appear as a regular browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def fetch_scorecard(self) -> Optional[str]:
        """Fetch the HTML scorecard"""
        url = f"{BASE_URL}/{self.match_id}/new-zealand-vs-england-1st-odi-england-in-new-zealand-2025-26"
        
        print(f"\n🔍 Fetching scorecard from: {url}")
        
        try:
            start_time = time.time()
            response = requests.get(url, headers=self.headers, timeout=15)
            elapsed = time.time() - start_time
            
            print(f"   ⏱️  Response time: {elapsed:.2f}s")
            print(f"   📊 Status code: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Success!")
                return response.text
            else:
                print(f"   ❌ Error: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"   ❌ Timeout after 15 seconds")
            return None
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return None
    
    def parse_scorecard(self, html: str) -> Dict:
        """Parse HTML scorecard and extract statistics"""
        soup = BeautifulSoup(html, 'html.parser')
        
        data = {
            "match_id": self.match_id,
            "timestamp": datetime.now().isoformat(),
            "match_status": "In Progress",
            "teams": {},
            "player_stats": {}  # Use dict for easier lookup by name
        }
        
        print("\n   📊 Extracting match data...")
        
        # Extract all player links to get full names
        player_links = soup.find_all('a', href=lambda x: x and 'player' in str(x))
        
        # Extract batting statistics from each innings
        print("\n   🏏 Extracting batting statistics...")
        
        # Find all rows with player batting data
        batting_rows = soup.find_all('tr')
        for row in batting_rows:
            cells = row.find_all('td')
            if len(cells) >= 8:
                try:
                    # Check if this is a batting row (has player link in first cell)
                    player_link = cells[0].find('a')
                    if not player_link:
                        continue
                    
                    player_name = player_link.get_text(strip=True)
                    dismissal_text = cells[1].get_text(strip=True)
                    runs_text = cells[2].get_text(strip=True)
                    balls_text = cells[3].get_text(strip=True)
                    fours_text = cells[5].get_text(strip=True)
                    sixes_text = cells[6].get_text(strip=True)
                    
                    # Initialize or update player entry
                    if player_name not in data["player_stats"]:
                        data["player_stats"][player_name] = {
                            "name": player_name,
                            "runs": 0,
                            "balls": 0,
                            "fours": 0,
                            "sixes": 0,
                            "wickets": 0,
                            "catches": 0,
                            "stumpings": 0,
                            "runOuts": 0
                        }
                    
                    # Update batting stats
                    player_stat = data["player_stats"][player_name]
                    player_stat["runs"] = int(runs_text) if runs_text.isdigit() else 0
                    player_stat["balls"] = int(balls_text) if balls_text.isdigit() else 0
                    player_stat["fours"] = int(fours_text) if fours_text.isdigit() else 0
                    player_stat["sixes"] = int(sixes_text) if sixes_text.isdigit() else 0
                    
                    print(f"      ✓ {player_name}: {player_stat['runs']} runs off {player_stat['balls']} balls")
                    
                    # Parse dismissal for fielding stats
                    dismissal_lower = dismissal_text.lower()
                    
                    # Extract catch - format: "c FielderName b BowlerName" or "c †WKName b BowlerName"
                    if 'c ' in dismissal_lower and ' b ' in dismissal_lower:
                        parts = dismissal_text.split()
                        c_index = next((i for i, p in enumerate(parts) if p.lower() == 'c'), None)
                        b_index = next((i for i, p in enumerate(parts) if p.lower() == 'b'), None)
                        
                        if c_index is not None and b_index is not None and c_index < b_index:
                            fielder_name = ' '.join(parts[c_index+1:b_index]).replace('†', '').strip()
                            # Initialize fielder if needed
                            if fielder_name and fielder_name not in data["player_stats"]:
                                data["player_stats"][fielder_name] = {
                                    "name": fielder_name,
                                    "runs": 0,
                                    "balls": 0,
                                    "fours": 0,
                                    "sixes": 0,
                                    "wickets": 0,
                                    "catches": 0,
                                    "stumpings": 0,
                                    "runOuts": 0
                                }
                            if fielder_name in data["player_stats"]:
                                data["player_stats"][fielder_name]["catches"] += 1
                                print(f"      ✓ Catch credited to {fielder_name}")
                    
                    # Extract stumping - format: "st †WKName b BowlerName"
                    if 'st ' in dismissal_lower or 'stumped' in dismissal_lower:
                        parts = dismissal_text.split()
                        st_index = next((i for i, p in enumerate(parts) if p.lower() in ['st', 'stumped']), None)
                        b_index = next((i for i, p in enumerate(parts) if p.lower() == 'b'), None)
                        
                        if st_index is not None and b_index is not None:
                            wk_name = ' '.join(parts[st_index+1:b_index]).replace('†', '').strip()
                            if wk_name and wk_name not in data["player_stats"]:
                                data["player_stats"][wk_name] = {
                                    "name": wk_name,
                                    "runs": 0,
                                    "balls": 0,
                                    "fours": 0,
                                    "sixes": 0,
                                    "wickets": 0,
                                    "catches": 0,
                                    "stumpings": 0,
                                    "runOuts": 0
                                }
                            if wk_name in data["player_stats"]:
                                data["player_stats"][wk_name]["stumpings"] += 1
                                print(f"      ✓ Stumping credited to {wk_name}")
                    
                    # Extract run out - format: "run out (FielderName)" or "run out (F1/F2)"
                    if 'run out' in dismissal_lower:
                        # Try to extract fielder names from parentheses
                        import re
                        ro_match = re.search(r'run out \(([^)]+)\)', dismissal_text, re.IGNORECASE)
                        if ro_match:
                            fielders = ro_match.group(1).split('/')
                            for fielder in fielders:
                                fielder_name = fielder.strip()
                                if fielder_name and fielder_name not in data["player_stats"]:
                                    data["player_stats"][fielder_name] = {
                                        "name": fielder_name,
                                        "runs": 0,
                                        "balls": 0,
                                        "fours": 0,
                                        "sixes": 0,
                                        "wickets": 0,
                                        "catches": 0,
                                        "stumpings": 0,
                                        "runOuts": 0
                                    }
                                if fielder_name in data["player_stats"]:
                                    data["player_stats"][fielder_name]["runOuts"] += 1
                                    print(f"      ✓ Run out credited to {fielder_name}")
                    
                except Exception as e:
                    print(f"      ⚠️  Error parsing batting row: {e}")
                    continue
        
        # Extract bowling statistics
        print("\n   🎯 Extracting bowling statistics...")
        
        # Find bowling table by looking for "Bowling" header
        for table in soup.find_all('table'):
            # Check if table has bowling data (look for O, M, R, W headers)
            headers = [th.get_text(strip=True) for th in table.find_all('th')]
            if 'O' in headers and 'W' in headers:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 5:
                        try:
                            player_link = cells[0].find('a')
                            if not player_link:
                                continue
                            
                            player_name = player_link.get_text(strip=True)
                            overs = cells[1].get_text(strip=True)
                            maidens = cells[2].get_text(strip=True)
                            runs_conceded = cells[3].get_text(strip=True)
                            wickets = cells[4].get_text(strip=True)
                            
                            # Initialize player if needed
                            if player_name not in data["player_stats"]:
                                data["player_stats"][player_name] = {
                                    "name": player_name,
                                    "runs": 0,
                                    "balls": 0,
                                    "fours": 0,
                                    "sixes": 0,
                                    "wickets": 0,
                                    "catches": 0,
                                    "stumpings": 0,
                                    "runOuts": 0
                                }
                            
                            # Update bowling stats
                            player_stat = data["player_stats"][player_name]
                            player_stat["wickets"] = int(wickets) if wickets.isdigit() else 0
                            player_stat["overs"] = overs
                            player_stat["runs_conceded"] = int(runs_conceded) if runs_conceded.isdigit() else 0
                            
                            print(f"      ✓ {player_name}: {player_stat['wickets']} wickets, {runs_conceded} runs")
                            
                        except Exception as e:
                            print(f"      ⚠️  Error parsing bowling row: {e}")
                            continue
        
        return data
    
    def save_snapshot(self, data: Dict):
        """Save scraped data snapshot"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.artifacts_dir}/espn_scorecard_{self.match_id}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n💾 Saved snapshot: {filename}")
        return filename
    
    def convert_to_csv(self, data: Dict) -> str:
        """Convert scraped data to CSV format for scoring"""
        print("\n📋 Converting to CSV format...")
        
        csv_lines = ["playerExternalId,runs,wickets,catches,stumpings,runOuts"]
        
        for player in data["player_stats"]:
            player_id = player["name"].lower().replace(" ", "-")
            runs = player.get("runs", 0)
            wickets = player.get("wickets", 0)
            catches = player.get("catches", 0)
            stumpings = player.get("stumpings", 0)
            run_outs = player.get("runOuts", 0)
            
            csv_lines.append(f"{player_id},{runs},{wickets},{catches},{stumpings},{run_outs}")
        
        csv_content = "\n".join(csv_lines)
        
        # Save CSV file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.artifacts_dir}/match_scores_{self.match_id}_{timestamp}.csv"
        
        with open(filename, 'w') as f:
            f.write(csv_content)
        
        print(f"   ✅ CSV saved: {filename}")
        return filename
    
    def run_single_scrape(self):
        """Run a single scrape operation"""
        html = self.fetch_scorecard()
        if not html:
            return None
        
        data = self.parse_scorecard(html)
        self.save_snapshot(data)
        self.convert_to_csv(data)
        
        return data
    
    def run_monitoring(self, interval: int = 600):
        """Monitor match continuously"""
        print(f"\n{'='*60}")
        print(f"🔴 STARTING LIVE MONITORING")
        print(f"   Match ID: {self.match_id}")
        print(f"   Interval: {interval} seconds ({interval/60:.0f} minutes)")
        print(f"   Press Ctrl+C to stop")
        print(f"{'='*60}")
        
        iteration = 1
        
        try:
            while True:
                print(f"\n\n{'='*60}")
                print(f"📊 ITERATION {iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*60}")
                
                data = self.run_single_scrape()
                
                if data:
                    print(f"\n✅ Data scraped successfully")
                    print(f"   Players found: {len(data['player_stats'])}")
                    print(f"   Match status: {data['match_status']}")
                else:
                    print(f"\n❌ Failed to scrape data")
                
                print(f"\n⏰ Next update in {interval} seconds...")
                time.sleep(interval)
                
                iteration += 1
                
        except KeyboardInterrupt:
            print(f"\n\n⏹️  Monitoring stopped after {iteration} iterations")
            print(f"💾 All data saved to: {self.artifacts_dir}")


def main():
    parser = argparse.ArgumentParser(description='Scrape ESPNcricinfo scorecard')
    parser.add_argument('--match-id', type=str, required=True,
                       help='ESPN match ID (e.g., 1491720)')
    parser.add_argument('--monitor', action='store_true',
                       help='Start continuous monitoring')
    parser.add_argument('--interval', type=int, default=600,
                       help='Monitoring interval in seconds (default: 600 = 10 min)')
    parser.add_argument('--odi', type=str, choices=['1', '2', '3'],
                       help='Use predefined ODI match (1, 2, or 3)')
    
    args = parser.parse_args()
    
    # If ODI number provided, use predefined match ID
    match_id = args.match_id
    if args.odi:
        match_id = MATCHES[args.odi]["match_id"]
        print(f"\n📋 Using ODI {args.odi}: {MATCHES[args.odi]['name']}")
    
    # Create scraper
    scraper = ESPNCricinfoScraper(match_id)
    
    print(f"\n{'='*60}")
    print(f"🏏 ESPNCRICINFO SCORECARD SCRAPER")
    print(f"   Match ID: {match_id}")
    print(f"{'='*60}")
    
    # Run scraping
    if args.monitor:
        scraper.run_monitoring(args.interval)
    else:
        scraper.run_single_scrape()
    
    print(f"\n✅ Scraping complete!")
    print(f"📁 Data saved to: {scraper.artifacts_dir}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
