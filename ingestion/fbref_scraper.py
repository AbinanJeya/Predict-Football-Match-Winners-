import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
from ingestion.db_utils import save_to_bronze

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FBRefScraper:
    def __init__(self):
        self.standings_url = "https://fbref.com/en/comps/9/Premier-League-Stats"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def scrape_season(self, year):
        logger.info(f"Scraping season {year}")
        try:
            data = requests.get(self.standings_url, headers=self.headers)
            data.raise_for_status()
            soup = BeautifulSoup(data.text, 'lxml')
            standings_tables = soup.select('table.stats_table')
            if not standings_tables:
                raise ValueError("Could not find standings table. FBRef might be blocking the request.")
            
            standings_table = standings_tables[0]
            links = [l.get("href") for l in standings_table.find_all('a')]
            links = [l for l in links if '/squads/' in l]
            team_urls = [f"https://fbref.com{l}" for l in links]
            
            previous_season = soup.select("a.prev")[0].get("href")
            self.standings_url = f"https://fbref.com{previous_season}"
            
            all_matches = []
            for team_url in team_urls:
                team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")
                logger.info(f"Scraping team: {team_name}")
                
                data = requests.get(team_url, headers=self.headers)
                matches = pd.read_html(data.text, match="Scores & Fixtures")[0]
                
                soup = BeautifulSoup(data.text, 'lxml')
                links = [l.get("href") for l in soup.find_all('a')]
                links = [l for l in links if l and 'all_comps/shooting/' in l]
                
                data = requests.get(f"https://fbref.com{links[0]}", headers=self.headers)
                shooting = pd.read_html(data.text, match="Shooting")[0]
                shooting.columns = shooting.columns.droplevel()
                
                try:
                    team_data = matches.merge(shooting[["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]], on="Date")
                except ValueError:
                    continue
                    
                team_data = team_data[team_data["Comp"] == "Premier League"]
                team_data["Season"] = year
                team_data["Team"] = team_name
                team_data.columns = [c.lower() for c in team_data.columns]
                
                all_matches.append(team_data)
                time.sleep(1)
                
            if all_matches:
                full_df = pd.concat(all_matches)
                save_to_bronze(full_df, "bronze_matches")
                logger.info(f"Saved {len(full_df)} matches to bronze layer.")

        except Exception as e:
            logger.error(f"Failed to scrape season {year}: {e}")
            logger.info("Attempting fallback to local matches.csv...")
            self.run_fallback()

    def run_fallback(self):
        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "matches.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path, index_col=0)
            df.columns = [c.lower() for c in df.columns]
            save_to_bronze(df, "bronze_matches")
            logger.info(f"Successfully loaded {len(df)} matches from local fallback into bronze layer.")
        else:
            logger.error("Fallback failed: matches.csv not found.")

if __name__ == "__main__":
    scraper = FBRefScraper()
    # Scrape current and last season for demo
    scraper.scrape_season(2023)
