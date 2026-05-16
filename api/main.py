from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import mlflow.sklearn
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Football Match Predictor API")

# Load model from MLflow
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

MODEL_NAME = "football_predictor"
MODEL_STAGE = "Production"

try:
    # Attempt to load the production model from MLflow
    model = mlflow.sklearn.load_model(f"models:/{MODEL_NAME}/latest")
    logger.info(f"Loaded model from MLflow: {MODEL_NAME}")
except Exception as e:
    logger.warning(f"Could not load model from MLflow: {e}")
    # Fallback to local file
    local_path = "api/model_checkpoint/latest_model.pkl"
    if os.path.exists(local_path):
        import joblib
        model = joblib.load(local_path)
        logger.info(f"Loaded model from local checkpoint: {local_path}")
    else:
        logger.error("No local model checkpoint found. Predictions will fail.")
        model = None

class MatchInput(BaseModel):
    venue_code: int
    opp_code: int
    hour: int
    day_code: int
    gf_rolling: float
    ga_rolling: float
    sh_rolling: float
    sot_rolling: float
    dist_rolling: float
    fk_rolling: float
    pk_rolling: float
    pkatt_rolling: float

@app.get("/")
def read_root():
    return {"message": "Football Match Predictor API is running"}

@app.post("/predict")
def predict(input_data: MatchInput):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Convert input to DataFrame
    df = pd.DataFrame([input_data.dict()])
    
    # Predict
    prediction = model.predict(df)[0]
    probability = model.predict_proba(df)[0][1]
    
    return {
        "prediction": int(prediction),
        "win_probability": float(probability)
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": model is not None}
