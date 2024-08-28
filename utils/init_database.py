import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def init_database():
    # Database connection parameters
    DB_PARAMS = {
        "dbname": "postgres",
        "user": "postgres",
        "password": "postgres",
        "host": "localhost",
        "port": "5432"
    }

    # Connect to PostgreSQL server
    conn = psycopg2.connect(**DB_PARAMS)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Create the table if it doesn't exist
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id BIGINT PRIMARY KEY,
        username VARCHAR(255) UNIQUE NOT NULL,
        alert_mode BOOLEAN DEFAULT FALSE,
        response_message BOOLEAN DEFAULT TRUE,
        state TEXT DEFAULT '',
        contacts JSONB DEFAULT '[]'::JSONB,
        daily_message JSONB DEFAULT '[]'::JSONB,
        contact_request JSONB DEFAULT '{}'::JSONB
    )
    """)

    print("Table 'users' created successfully (if it didn't exist).")

    # Close communication with the database
    cur.close()
    conn.close()