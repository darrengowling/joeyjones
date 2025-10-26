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
            "match_status": "unknown",
            "teams": {},
            "player_stats": []
        }
        
        # Extract match status
        status_elem = soup.find('span', class_='ds-text-tight-s')
        if status_elem:
            data["match_status"] = status_elem.get_text(strip=True)
        
        # Extract team scores
        score_elems = soup.find_all('div', class_='ds-text-compact-xxs')
        for elem in score_elems:
            text = elem.get_text(strip=True)
            if "/" in text and "(" in text:
                # This is likely a score
                print(f"   Found score: {text}")
        
        # Extract batting statistics
        print("\n   📊 Extracting batting statistics...")
        batting_tables = soup.find_all('table', class_='ds-table')
        
        for table in batting_tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # Skip header
                cols = row.find_all('td')
                if len(cols) >= 8:
                    try:
                        player_link = cols[0].find('a')
                        if not player_link:
                            continue
                        
                        player_name = player_link.get_text(strip=True)
                        runs = cols[2].get_text(strip=True)
                        balls = cols[3].get_text(strip=True)
                        fours = cols[5].get_text(strip=True)
                        sixes = cols[6].get_text(strip=True)
                        
                        # Check dismissal for catches/stumpings/run-outs
                        dismissal = cols[1].get_text(strip=True).lower()
                        caught = 1 if ('c ' in dismissal or 'caught' in dismissal) else 0
                        stumped = 1 if ('st ' in dismissal or 'stumped' in dismissal) else 0
                        run_out = 1 if ('run out' in dismissal or 'ro ' in dismissal) else 0
                        
                        player_stat = {
                            "name": player_name,
                            "role": "batsman",
                            "runs": int(runs) if runs.isdigit() else 0,
                            "balls": int(balls) if balls.isdigit() else 0,
                            "fours": int(fours) if fours.isdigit() else 0,
                            "sixes": int(sixes) if sixes.isdigit() else 0,
                            "dismissal": dismissal
                        }
                        
                        data["player_stats"].append(player_stat)
                        print(f"      ✓ {player_name}: {runs} runs")
                        
                    except Exception as e:
                        continue
        
        # Extract bowling statistics
        print("\n   🎯 Extracting bowling statistics...")
        bowling_sections = soup.find_all('table')
        
        for table in bowling_sections:
            # Check if this is a bowling table
            header = table.find('th')
            if header and 'Bowling' in str(header):
                rows = table.find_all('tr')
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 6:
                        try:
                            player_link = cols[0].find('a')
                            if not player_link:
                                continue
                            
                            player_name = player_link.get_text(strip=True)
                            overs = cols[1].get_text(strip=True)
                            runs_conceded = cols[3].get_text(strip=True)
                            wickets = cols[4].get_text(strip=True)
                            
                            # Find or create player stat entry
                            player_stat = next((p for p in data["player_stats"] if p["name"] == player_name), None)
                            if not player_stat:
                                player_stat = {
                                    "name": player_name,
                                    "role": "bowler",
                                    "runs": 0
                                }
                                data["player_stats"].append(player_stat)
                            
                            player_stat["wickets"] = int(wickets) if wickets.isdigit() else 0
                            player_stat["overs"] = overs
                            player_stat["runs_conceded"] = int(runs_conceded) if runs_conceded.isdigit() else 0
                            
                            print(f"      ✓ {player_name}: {wickets} wickets")
                            
                        except Exception as e:
                            continue
        
        # Extract fielding statistics (catches, stumpings)
        print("\n   🧤 Extracting fielding statistics...")
        # Fielding stats are in dismissal text - parse "c †Latham" = catch by Latham
        for stat in data["player_stats"]:
            if "dismissal" in stat:
                dismissal_text = stat["dismissal"]
                
                # Extract fielders from dismissal text
                if "c " in dismissal_text or "caught" in dismissal_text:
                    # Find the fielder name
                    parts = dismissal_text.split()
                    for i, part in enumerate(parts):
                        if part == 'c' and i + 1 < len(parts):
                            fielder_name = parts[i + 1].replace('†', '').strip()
                            # Add catch to this fielder
                            fielder_stat = next((p for p in data["player_stats"] if fielder_name in p["name"]), None)
                            if fielder_stat:
                                fielder_stat["catches"] = fielder_stat.get("catches", 0) + 1
                                print(f"      ✓ Catch credited to {fielder_name}")
        
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
