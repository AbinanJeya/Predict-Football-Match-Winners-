import sys
import os
import time
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import logging

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ingestion.db_utils import save_to_bronze

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FBRefStealthScraper:
    def __init__(self):
        self.standings_url = "https://fbref.com/en/comps/9/Premier-League-Stats"

    def scrape_season(self, year):
        logger.info(f"🚀 Starting Manual Stealth Scrape for season {year}...")
        
        with sync_playwright() as p:
            # Launch with a realistic user agent and viewport
            browser = p.chromium.launch(headless=True)
            
            # Create a context that mimics a real browser
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            
            page = context.new_page()
            
            try:
                # 1. Get Standings
                logger.info(f"Accessing: {self.standings_url}")
                # We add a referer to look even more human
                page.goto(self.standings_url, wait_until="domcontentloaded", timeout=60000)
                time.sleep(3) 
                
                content = page.content()
                soup = BeautifulSoup(content, 'lxml')
                
                standings_tables = soup.select('table.stats_table')
                if not standings_tables:
                    logger.error("Could not find standings table. FBRef might still be blocking.")
                    return
                    
                standings_table = standings_tables[0]
                links = [l.get("href") for l in standings_table.find_all('a')]
                links = [l for l in links if '/squads/' in l]
                team_urls = [f"https://fbref.com{l}" for l in links]
                
                all_matches = []
                # Scraping top 5 teams for demo stability
                for team_url in team_urls[:5]: 
                    team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")
                    logger.info(f"Scraping team: {team_name}")
                    
                    page.goto(team_url, wait_until="domcontentloaded")
                    time.sleep(2)
                    
                    html = page.content()
                    matches_list = pd.read_html(html, match="Scores & Fixtures")
                    if not matches_list:
                        continue
                    matches = matches_list[0]
                    
                    soup = BeautifulSoup(html, 'lxml')
                    links = [l.get("href") for l in soup.find_all('a')]
                    shooting_links = [l for l in links if l and 'all_comps/shooting/' in l]
                    
                    if shooting_links:
                        page.goto(f"https://fbref.com{shooting_links[0]}", wait_until="domcontentloaded")
                        time.sleep(2)
                        
                        shooting_html = page.content()
                        shooting_list = pd.read_html(shooting_html, match="Shooting")
                        if shooting_list:
                            shooting = shooting_list[0]
                            shooting.columns = shooting.columns.droplevel()
                            
                            try:
                                team_data = matches.merge(shooting[["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]], on="Date")
                                team_data = team_data[team_data["Comp"] == "Premier League"]
                                team_data["Season"] = year
                                team_data["Team"] = team_name
                                team_data.columns = [c.lower() for c in team_data.columns]
                                all_matches.append(team_data)
                                logger.info(f"✅ Successfully scraped {team_name}")
                            except Exception as e:
                                logger.warning(f"Merge failed for {team_name}: {e}")
                                
                if all_matches:
                    full_df = pd.concat(all_matches)
                    save_to_bronze(full_df, "bronze_matches")
                    logger.info(f"🎉 Saved {len(full_df)} current matches from 2024 to database.")
                    
            except Exception as e:
                logger.error(f"❌ Scrape Failed: {e}")
            finally:
                browser.close()

if __name__ == "__main__":
    scraper = FBRefStealthScraper()
    scraper.scrape_season(2024)
