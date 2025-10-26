#!/root/.venv/bin/python3
"""
NDTV Sports Scorecard Scraper
==============================
Scrapes live cricket scorecard data from NDTV Sports.
Much cleaner HTML structure than ESPNcricinfo!

Usage:
    python scrape_ndtv.py --url <scorecard-url>
    python scrape_ndtv.py --url <scorecard-url> --monitor --interval 600
"""

import requests
from bs4 import BeautifulSoup
import json
import argparse
import time
import sys
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

# NDTV scorecard URL for NZ vs ENG ODI 1
DEFAULT_URL = "https://sports.ndtv.com/cricket/nz-vs-eng-scorecard-live-cricket-score-england-in-new-zealand-3-odi-series-2025-1st-odi-nzen10262025262746"

# Player name mapping to database IDs
PLAYER_MAPPING = {
    # England
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
    
    # New Zealand
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
    "Zakary Foulkes": "zak-foulkes",  # Alternative spelling
    "Nathan Smith": "nathan-smith"
}


class NDTVScraper:
    """Scraper for NDTV Sports scorecards"""
    
    def __init__(self, url: str):
        self.url = url
        self.artifacts_dir = "/app/artifacts"
        os.makedirs(self.artifacts_dir, exist_ok=True)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def fetch_scorecard(self) -> Optional[str]:
        """Fetch the HTML scorecard"""
        print(f"\n🔍 Fetching scorecard from NDTV Sports...")
        
        try:
            start_time = time.time()
            response = requests.get(self.url, headers=self.headers, timeout=15)
            elapsed = time.time() - start_time
            
            print(f"   ⏱️  Response time: {elapsed:.2f}s")
            print(f"   📊 Status code: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Success!")
                return response.text
            else:
                print(f"   ❌ Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return None
    
    def parse_scorecard(self, html: str) -> Dict:
        """Parse HTML scorecard and extract statistics"""
        soup = BeautifulSoup(html, 'html.parser')
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "match_status": "In Progress",
            "player_stats": {}  # Use dict for easier lookup
        }
        
        print("\n   📊 Extracting player statistics...")
        
        # Find all batting rows
        print("\n   🏏 Parsing batting data...")
        batting_rows = soup.find_all('tr')
        
        for row in batting_rows:
            cells = row.find_all('td')
            if len(cells) >= 6:
                try:
                    # Check if this is a batsman row (has player link)
                    player_link = cells[0].find('a')
                    if not player_link:
                        continue
                    
                    player_name = player_link.get_text(strip=True)
                    
                    # Get batting stats
                    runs = cells[1].get_text(strip=True)
                    balls = cells[2].get_text(strip=True)
                    
                    # Initialize player
                    if player_name not in data["player_stats"]:
                        data["player_stats"][player_name] = {
                            "name": player_name,
                            "runs": 0,
                            "wickets": 0,
                            "catches": 0,
                            "stumpings": 0,
                            "runOuts": 0
                        }
                    
                    # Update batting stats
                    player_stat = data["player_stats"][player_name]
                    player_stat["runs"] = int(runs) if runs.isdigit() else 0
                    player_stat["balls"] = int(balls) if balls.isdigit() else 0
                    
                    print(f"      ✓ {player_name}: {player_stat['runs']} runs")
                    
                    # Parse dismissal for fielding stats
                    # Look for dismissal info (might be in a div with arrow icon)
                    dismissal_div = cells[0].find('div', class_='arw_dwn')
                    if dismissal_div:
                        dismissal_text = dismissal_div.get_text(strip=True)
                        self._parse_dismissal(dismissal_text, data["player_stats"])
                    
                except Exception as e:
                    continue
        
        # Find bowling table
        print("\n   🎯 Parsing bowling data...")
        
        # Look for "Bowling" header in tables
        for table in soup.find_all('table'):
            headers = [th.get_text(strip=True) for th in table.find_all('th')]
            
            # Check if this is bowling table (has O, M, R, W, Econ headers)
            if 'Bowling' in str(table) or ('O' in headers and 'W' in headers):
                rows = table.find_all('tr')
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
                                    "wickets": 0,
                                    "catches": 0,
                                    "stumpings": 0,
                                    "runOuts": 0
                                }
                            
                            # Update bowling stats
                            player_stat = data["player_stats"][player_name]
                            player_stat["wickets"] = int(wickets) if wickets.isdigit() else 0
                            player_stat["overs"] = overs
                            
                            print(f"      ✓ {player_name}: {player_stat['wickets']} wickets")
                            
                        except Exception as e:
                            continue
        
        print(f"\n   📊 Total players tracked: {len(data['player_stats'])}")
        return data
    
    def _parse_dismissal(self, dismissal_text: str, player_stats: Dict):
        """Parse dismissal text to extract fielding stats"""
        dismissal_lower = dismissal_text.lower()
        
        # Pattern: "c FielderName b BowlerName"
        if 'c ' in dismissal_lower and ' b ' in dismissal_lower:
            match = re.search(r'c\s+([^b]+?)\s+b\s+', dismissal_text, re.IGNORECASE)
            if match:
                fielder_name = match.group(1).strip().replace('†', '').replace('Wk', '')
                
                # Find matching player (handle partial names)
                for player_name in player_stats:
                    if fielder_name in player_name or player_name in fielder_name:
                        player_stats[player_name]["catches"] += 1
                        print(f"      ✓ Catch credited to {player_name}")
                        break
                else:
                    # Fielder not in stats yet, create entry
                    if fielder_name:
                        player_stats[fielder_name] = {
                            "name": fielder_name,
                            "runs": 0,
                            "wickets": 0,
                            "catches": 1,
                            "stumpings": 0,
                            "runOuts": 0
                        }
                        print(f"      ✓ Catch credited to {fielder_name} (new entry)")
        
        # Pattern: "st †WKName b BowlerName" or "stumped"
        if 'st ' in dismissal_lower or 'stumped' in dismissal_lower:
            match = re.search(r'st\s+†?\s*([^b]+?)\s+b\s+', dismissal_text, re.IGNORECASE)
            if match:
                wk_name = match.group(1).strip().replace('†', '').replace('Wk', '')
                
                for player_name in player_stats:
                    if wk_name in player_name or player_name in wk_name:
                        player_stats[player_name]["stumpings"] += 1
                        print(f"      ✓ Stumping credited to {player_name}")
                        break
        
        # Pattern: "run out (Fielder1/Fielder2)" or "run out (Fielder)"
        if 'run out' in dismissal_lower:
            match = re.search(r'run out\s*\(([^)]+)\)', dismissal_text, re.IGNORECASE)
            if match:
                fielders = match.group(1).split('/')
                for fielder in fielders:
                    fielder_name = fielder.strip()
                    
                    for player_name in player_stats:
                        if fielder_name in player_name or player_name in fielder_name:
                            player_stats[player_name]["runOuts"] += 1
                            print(f"      ✓ Run out credited to {player_name}")
                            break
    
    def save_snapshot(self, data: Dict):
        """Save scraped data snapshot"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.artifacts_dir}/ndtv_scorecard_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n💾 Saved snapshot: {filename}")
        return filename
    
    def convert_to_csv(self, data: Dict) -> str:
        """Convert scraped data to CSV format for scoring"""
        print("\n📋 Converting to CSV format...")
        
        csv_lines = ["playerExternalId,runs,wickets,catches,stumpings,runOuts"]
        
        for player_name, stats in data["player_stats"].items():
            # Map to database ID
            player_id = PLAYER_MAPPING.get(player_name)
            if not player_id:
                # Fallback: convert name to ID format
                player_id = player_name.lower().replace(" ", "-").replace(".", "")
                print(f"   ⚠️  No mapping for {player_name}, using: {player_id}")
            
            runs = stats.get("runs", 0)
            wickets = stats.get("wickets", 0)
            catches = stats.get("catches", 0)
            stumpings = stats.get("stumpings", 0)
            run_outs = stats.get("runOuts", 0)
            
            # Only include players with some activity
            if runs > 0 or wickets > 0 or catches > 0 or stumpings > 0 or run_outs > 0:
                csv_lines.append(f"{player_id},{runs},{wickets},{catches},{stumpings},{run_outs}")
                print(f"   ✓ {player_name}: R{runs} W{wickets} C{catches} St{stumpings} RO{run_outs}")
        
        csv_content = "\n".join(csv_lines)
        
        # Save CSV file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.artifacts_dir}/match_scores_ndtv_{timestamp}.csv"
        
        with open(filename, 'w') as f:
            f.write(csv_content)
        
        print(f"\n   💾 CSV saved: {filename}")
        print(f"   📊 Total players in CSV: {len(csv_lines) - 1}")
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
        print(f"   Source: NDTV Sports")
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
                else:
                    print(f"\n❌ Failed to scrape data")
                
                print(f"\n⏰ Next update in {interval} seconds...")
                time.sleep(interval)
                
                iteration += 1
                
        except KeyboardInterrupt:
            print(f"\n\n⏹️  Monitoring stopped after {iteration} iterations")
            print(f"💾 All data saved to: {self.artifacts_dir}")


def main():
    parser = argparse.ArgumentParser(description='Scrape NDTV Sports scorecard')
    parser.add_argument('--url', type=str, default=DEFAULT_URL,
                       help='NDTV scorecard URL')
    parser.add_argument('--monitor', action='store_true',
                       help='Start continuous monitoring')
    parser.add_argument('--interval', type=int, default=600,
                       help='Monitoring interval in seconds (default: 600 = 10 min)')
    
    args = parser.parse_args()
    
    # Create scraper
    scraper = NDTVScraper(args.url)
    
    print(f"\n{'='*60}")
    print(f"🏏 NDTV SPORTS SCORECARD SCRAPER")
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
