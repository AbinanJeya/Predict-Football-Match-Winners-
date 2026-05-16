import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mlflow
import mlflow.sklearn
import pandas as pd
import xgboost as xgb
from sklearn.metrics import precision_score, accuracy_score
from ingestion.db_utils import read_from_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set MLflow tracking URI
mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
mlflow.set_experiment("football_match_prediction")

def train_model():
    logger.info("Loading features from Gold layer...")
    df = read_from_db("SELECT * FROM gold_features")
    
    # Dynamic split based on dates
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    
    # Use the last 20% of the data for testing
    split_idx = int(len(df) * 0.8)
    train = df.iloc[:split_idx]
    test = df.iloc[split_idx:]
    
    logger.info(f"Split data into {len(train)} training and {len(test)} testing samples.")
    
    predictors = ["venue_code", "opp_code", "hour", "day_code", 
                  "gf_rolling", "ga_rolling", "sh_rolling", 
                  "sot_rolling", "dist_rolling", "fk_rolling", 
                  "pk_rolling", "pkatt_rolling"]
    
    X_train, y_train = train[predictors], train["target"]
    X_test, y_test = test[predictors], test["target"]
    
    with mlflow.start_run():
        params = {
            "n_estimators": 100,
            "max_depth": 5,
            "learning_rate": 0.1,
            "random_state": 1
        }
        
        model = xgb.XGBClassifier(**params)
        model.fit(X_train, y_train)
        
        preds = model.predict(X_test)
        precision = precision_score(y_test, preds)
        accuracy = accuracy_score(y_test, preds)
        
        logger.info(f"Precision: {precision}")
        logger.info(f"Accuracy: {accuracy}")
        
        # Log metrics and model
        mlflow.log_params(params)
        mlflow.log_metric("precision", precision)
        mlflow.log_metric("accuracy", accuracy)
        
        mlflow.sklearn.log_model(model, "model", registered_model_name="football_predictor")
        
        # Local fallback for API stability
        os.makedirs("api/model_checkpoint", exist_ok=True)
        import joblib
        joblib.dump(model, "api/model_checkpoint/latest_model.pkl")
        
        logger.info("Model trained, logged to MLflow, and saved locally for API.")

if __name__ == "__main__":
    train_model()
