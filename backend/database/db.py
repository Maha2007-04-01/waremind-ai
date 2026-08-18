import sqlite3
import os
import logging
from contextlib import contextmanager
from config import Config

logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Creates and returns a thread-safe SQLite database connection with row_factory enabled.
    """
    db_path = Config.DATABASE_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    # Enable SQLite foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@contextmanager
def db_transaction():
    """
    Context manager for database transactions ensuring automatic commit/rollback.
    """
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database transaction error: {str(e)}")
        raise e
    finally:
        conn.close()

def check_db_connection():
    """
    Verifies SQLite database connectivity by executing a lightweight query.
    Returns tuple: (is_connected: bool, message: str)
    """
    try:
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        return True, "connected"
    except Exception as e:
        logger.error(f"Database connection health check failed: {str(e)}")
        return False, f"error: {str(e)}"

def init_db():
    """
    Initializes the SQLite database schema if tables do not exist.
    """
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    if not os.path.exists(schema_path):
        logger.warning(f"Schema file not found at {schema_path}")
        return

    with db_transaction() as conn:
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())
    logger.info("Database schema initialized successfully.")
