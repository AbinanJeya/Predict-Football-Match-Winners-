# 📑 Technical Project Specification: Football Prediction Platform

This document provides a detailed architectural breakdown of the **Football Match Predictor**, a production-grade machine learning platform.

---

## 🏗️ 1. System Architecture
The platform follows a **Medallion Architecture** for data processing, ensuring data integrity and lineage.

### A. Data Layers (PostgreSQL)
*   **Bronze Layer (Raw)**: Stores the raw ingestion results from both the FBRef Scraper and the Official League CSVs. No cleaning is performed here to allow for full re-processing if schemas change.
*   **Silver Layer (Cleaned)**: Data is normalized. Strings (Team names, Venues) are mapped to numeric category codes. Temporal features (Hour, Day of Week) are extracted.
*   **Gold Layer (Feature Store)**: The high-value layer used for ML. It contains engineered features like **3-match rolling averages** for scoring, shots, and defensive metrics.

---

## ⚙️ 2. Data Engineering Pipeline
The pipeline is orchestrated using **Prefect** to ensure reliable execution.

### Ingestion Strategy
1.  **Primary (Historical)**: Local CSV loading for baseline training data.
2.  **Secondary (Live Scraper)**: A Playwright-based scraper (with manual stealth config) designed to bypass anti-bot protections.
3.  **Tertiary (Official Feed)**: A direct downloader for official league results (`football-data.co.uk`) to ensure 100% uptime for current season data.

### Feature Engineering
The model's performance relies on **contextual performance indicators**:
*   **Rolling Averages**: Instead of raw match stats, the model looks at the last 3 matches to gauge current form.
*   **Categorical Encoding**: Teams and opponents are encoded as unique integer IDs.
*   **Time-of-Day Features**: Extracting match start times to capture potential day/night performance variances.

---

## 🧠 3. Machine Learning Model
*   **Algorithm**: **XGBoost Classifier** (Gradient Boosted Decision Trees).
*   **Training Split**: A dynamic 80/20 train/test split.
*   **Evaluation Metrics**: 
    *   **Accuracy**: Overall correctness of the win/not-win prediction.
    *   **Precision**: Focuses on minimizing "False Wins" (Crucial for betting/analytics reliability).
*   **Persistence**: Models are saved as `.pkl` files and registered in the **MLflow Model Registry**.

---

## 🧪 4. MLOps & Infrastructure
*   **MLflow**: Every training run logs hyperparameters (`learning_rate`, `n_estimators`), metrics, and the model artifact.
*   **Docker**: 
    *   `football_db`: PostgreSQL 15 instance (Port 5433).
    *   `mlflow_server`: Tracking server for experiment lineage.
    *   `football_api`: FastAPI container for production inference.
*   **API Dual-Loading**: The prediction API is designed for **High Availability**. It attempts to load the latest model from the MLflow registry; if unreachable, it seamlessly falls back to a local model checkpoint.

---

## 🖥️ 5. Control Center (GUI)
The **Mission Control Dashboard** (Tkinter) acts as the system's brain:
*   **Background Threading**: Pipeline runs (Ingestion/Training) are executed in separate threads to keep the UI responsive.
*   **Subprocess Streaming**: Console logs from the Python scripts are piped directly into the GUI's log window.
*   **State Management**: The dashboard detects when a pipeline run finishes and triggers a data refresh.

---

## 📂 6. File Structure
```text
├── api/                  # FastAPI inference service
├── docs/                 # Documentation assets & screenshots
├── ingestion/            # Scrapers and data loaders
├── models/               # ML training and model artifacts
├── pipelines/            # Prefect orchestrator workflows
├── scripts/              # GUI Dashboard and setup utilities
├── transformation/       # Data cleaning and feature engineering
├── docker-compose.yml    # Infrastructure orchestration
├── requirements.txt      # Dependency management
└── .env                  # Environment configuration
```

---

**Author**: Abinan Jeyaratnam  
**Version**: 1.0.0  
**Last Updated**: 2026-05-15
