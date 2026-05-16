import psycopg2
from ingestion.db_utils import DB_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    # Create tables (SQL schema)
    # Note: Pandas to_sql handles this, but explicit schema can be added here for production.
    
    logger.info("Database setup complete.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    setup_database()
