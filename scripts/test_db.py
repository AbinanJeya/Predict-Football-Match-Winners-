import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5433/football_match_data")

def test_connection():
    print(f"Testing connection to: {DB_URL}")
    try:
        conn = psycopg2.connect(DB_URL)
        print("✅ Connection successful!")
        conn.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nPossible solutions:")
        print("1. Ensure your Docker containers are running: 'docker-compose up -d'")
        print("2. Check if a local PostgreSQL instance is already running on port 5432 with different credentials.")
        print("3. Update the credentials in your .env file.")

if __name__ == "__main__":
    test_connection()
