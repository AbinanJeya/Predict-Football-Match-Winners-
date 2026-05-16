import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import logging
from ingestion.db_utils import get_engine, read_from_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def transform_to_silver():
    logger.info("Starting transformation to Silver layer...")
    
    # Load raw data
    try:
        df = read_from_db("SELECT * FROM bronze_matches")
    except Exception as e:
        logger.error(f"Error reading from bronze layer: {e}")
        return

    if df.empty:
        logger.warning("Bronze layer is empty. Skipping transformation.")
        return
    
    # Cleaning
    df["date"] = pd.to_datetime(df["date"])
    df["venue_code"] = df["venue"].astype("category").cat.codes
    df["opp_code"] = df["opponent"].astype("category").cat.codes
    df["hour"] = df["time"].str.replace(":.+", "", regex=True).astype("int")
    df["day_code"] = df["date"].dt.dayofweek
    df["target"] = (df["result"] == "W").astype("int")
    
    # Normalize team names if necessary (FBRef can be inconsistent)
    # Mapping could be added here
    
    # Save to Silver Layer
    engine = get_engine()
    df.to_sql("silver_matches", engine, if_exists='replace', index=False)
    logger.info("Saved transformed data to silver_matches table.")

def generate_features():
    logger.info("Generating features for Gold layer (Feature Store)...")
    
    df = read_from_db("SELECT * FROM silver_matches")
    df = df.sort_values("date")
    
    def rolling_averages(group, cols, new_cols):
        group = group.sort_values("date")
        rolling_stats = group[cols].rolling(3, closed='left').mean()
        group[new_cols] = rolling_stats
        group = group.dropna(subset=new_cols)
        return group

    cols = ["gf", "ga", "sh", "sot", "dist", "fk", "pk", "pkatt"]
    new_cols = [f"{c}_rolling" for c in cols]
    
    df_rolling = df.groupby("team").apply(lambda x: rolling_averages(x, cols, new_cols))
    df_rolling = df_rolling.droplevel('team')
    df_rolling.index = range(df_rolling.shape[0])
    
    # Save to Gold Layer (Feature Store)
    engine = get_engine()
    df_rolling.to_sql("gold_features", engine, if_exists='replace', index=False)
    logger.info("Saved engineered features to gold_features table.")

if __name__ == "__main__":
    transform_to_silver()
    generate_features()
