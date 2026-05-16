import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prefect import flow, task
from ingestion.fbref_scraper import FBRefScraper
from transformation.process_data import transform_to_silver, generate_features
from models.train import train_model
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@task
def run_ingestion():
    scraper = FBRefScraper()
    scraper.scrape_season(2023)
    scraper.scrape_season(2022)

@task
def run_transformation():
    transform_to_silver()
    generate_features()

@task
def run_training():
    train_model()

@flow(name="Football Prediction Pipeline")
def football_pipeline():
    logger.info("Starting Football Prediction Pipeline...")
    ingest = run_ingestion()
    transform = run_transformation(wait_for=[ingest])
    train = run_training(wait_for=[transform])
    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    football_pipeline()
