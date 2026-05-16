import sys
import os
import requests
import pandas as pd
import logging

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ingestion.db_utils import save_to_bronze

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_and_map_data():
    # URL for Premier League 2023/2024
    url = "https://www.football-data.co.uk/mmz4281/2324/E0.csv"
    logger.info(f"Downloading 2023/2024 season data...")
    
    try:
        df = pd.read_csv(url)
        logger.info(f"Mapping {len(df)} matches to model schema...")
        
        all_rows = []
        
        for _, match in df.iterrows():
            # Row for Home Team
            home_row = {
                "date": match["Date"],
                "time": match["Time"] if "Time" in match else "00:00",
                "comp": "Premier League",
                "round": "Matchweek Unknown",
                "day": pd.to_datetime(match["Date"], dayfirst=True).day_name()[:3],
                "venue": "Home",
                "result": "W" if match["FTR"] == "H" else ("L" if match["FTR"] == "A" else "D"),
                "gf": match["FTHG"],
                "ga": match["FTAG"],
                "opponent": match["AwayTeam"],
                "sh": match["HS"],
                "sot": match["HST"],
                "dist": 16.0, # Approximate as not in this dataset
                "fk": 0.0,
                "pk": 0.0,
                "pkatt": 0.0,
                "referee": match["Referee"],
                "season": 2024,
                "team": match["HomeTeam"]
            }
            
            # Row for Away Team
            away_row = {
                "date": match["Date"],
                "time": match["Time"] if "Time" in match else "00:00",
                "comp": "Premier League",
                "round": "Matchweek Unknown",
                "day": pd.to_datetime(match["Date"], dayfirst=True).day_name()[:3],
                "venue": "Away",
                "result": "W" if match["FTR"] == "A" else ("L" if match["FTR"] == "H" else "D"),
                "gf": match["FTAG"],
                "ga": match["FTHG"],
                "opponent": match["HomeTeam"],
                "sh": match["AS"],
                "sot": match["AST"],
                "dist": 16.0,
                "fk": 0.0,
                "pk": 0.0,
                "pkatt": 0.0,
                "referee": match["Referee"],
                "season": 2024,
                "team": match["AwayTeam"]
            }
            
            all_rows.append(home_row)
            all_rows.append(away_row)
            
        mapped_df = pd.DataFrame(all_rows)
        # Convert date to standard format
        mapped_df["date"] = pd.to_datetime(mapped_df["date"], dayfirst=True).dt.strftime('%Y-%m-%d')
        
        # Save to the main bronze table
        save_to_bronze(mapped_df, "bronze_matches")
        logger.info(f"🎉 Successfully ingested {len(mapped_df)} new match records into the Bronze Layer.")
        
    except Exception as e:
        logger.error(f"Failed to map data: {e}")

if __name__ == "__main__":
    download_and_map_data()
