import os
from sqlalchemy import create_engine
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5433/football_match_data")

def get_engine():
    return create_engine(DB_URL)

def save_to_bronze(df, table_name):
    engine = get_engine()
    df.to_sql(table_name, engine, if_exists='append', index=False)

def read_from_db(query):
    engine = get_engine()
    return pd.read_sql(query, engine)
