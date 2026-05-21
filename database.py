import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    """
    Opens and returns a new psycopg2 connection using the DATABASE_URL env variable.
    Usage:
        conn = get_connection()
        cur  = conn.cursor()
        ...
        conn.close()
    """
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Add it to your .env file locally or to Render's Environment Variables."
        )
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn
