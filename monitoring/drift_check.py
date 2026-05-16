import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from ingestion.db_utils import read_from_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_for_drift():
    logger.info("Checking for data drift...")
    
    # Load gold features (production data)
    df = read_from_db("SELECT * FROM gold_features")
    
    # Simple drift check: compare mean of features in the last 3 months vs previous data
    # This is a placeholder for more advanced drift detection (like Kolmogorov-Smirnov test)
    
    recent_data = df[df["date"] > df["date"].max() - pd.Timedelta(days=90)]
    historical_data = df[df["date"] <= df["date"].max() - pd.Timedelta(days=90)]
    
    if len(recent_data) == 0 or len(historical_data) == 0:
        logger.info("Not enough data to check for drift.")
        return
    
    drift_detected = False
    predictors = ["gf_rolling", "ga_rolling", "sh_rolling", "sot_rolling"]
    
    for col in predictors:
        recent_mean = recent_data[col].mean()
        hist_mean = historical_data[col].mean()
        diff = abs(recent_mean - hist_mean) / hist_mean
        
        if diff > 0.2: # 20% drift threshold
            logger.warning(f"Drift detected in feature {col}: {diff:.2%}")
            drift_detected = True
            
    if not drift_detected:
        logger.info("No significant drift detected.")

if __name__ == "__main__":
    check_for_drift()
