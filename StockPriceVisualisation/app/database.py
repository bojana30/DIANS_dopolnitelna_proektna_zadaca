import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "stock_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
}

def get_db_connection():
    """Returns a new database connection."""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def initialize_database():
    """Ensures the stock_data table exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_data (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10),
            date TIMESTAMP,
            close FLOAT,
            volume BIGINT
        )
    ''')
    conn.commit()
    conn.close()