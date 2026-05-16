import sys
import os

# Add project root to sys.path BEFORE other local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import joblib
from ingestion.db_utils import read_from_db

def view_recent_predictions():
    print("--- Football Prediction Validation Viewer ---")
    
    # 1. Load data from Feature Store
    print("Loading test features from database...")
    try:
        df = read_from_db("SELECT * FROM gold_features")
    except Exception as e:
        print(f"❌ Error reading from database: {e}")
        return

    if df.empty:
        print("❌ Error: gold_features table is empty. Please run the pipeline first.")
        return

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date", ascending=False)
    
    # Use the same 20% test split logic
    split_idx = int(len(df) * 0.2)
    test_df = df.iloc[:split_idx].copy()
    
    # 2. Load the trained model
    model_path = "api/model_checkpoint/latest_model.pkl"
    if not os.path.exists(model_path):
        print(f"❌ Error: Model not found at {model_path}. Please run the pipeline first.")
        return
    
    model = joblib.load(model_path)
    
    # 3. Define predictors
    predictors = ["venue_code", "opp_code", "hour", "day_code", 
                  "gf_rolling", "ga_rolling", "sh_rolling", 
                  "sot_rolling", "dist_rolling", "fk_rolling", 
                  "pk_rolling", "pkatt_rolling"]
    
    # 4. Make predictions
    print("Generating predictions for recent matches...")
    test_df["predicted_win"] = model.predict(test_df[predictors])
    test_df["win_probability"] = model.predict_proba(test_df[predictors])[:, 1]
    
    # 5. Create a human-readable results table
    results = test_df[["date", "team", "opponent", "result", "predicted_win", "win_probability"]].head(20)
    
    print("\n--- Latest 20 Predictions vs Actuals ---")
    print(results.to_string(index=False))
    
    # Calculate accuracy on this subset
    correct = (results["result"] == "W") == (results["predicted_win"] == 1)
    accuracy = correct.mean()
    print(f"\nSubset Accuracy: {accuracy:.2%}")
    print("\nNote: 'predicted_win' = 1 means the model thought the team would win.")

if __name__ == "__main__":
    view_recent_predictions()
