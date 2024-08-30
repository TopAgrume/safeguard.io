import os
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager

# Database connection parameters
DB_PARAMS = {
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

# Create a connection pool
pool = SimpleConnectionPool(1, 20, **DB_PARAMS)


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.

    Yields:
        psycopg2.extensions.connection: A database connection from the pool.
    """
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)


@contextmanager
def get_db_cursor(commit=False):
    """
    Context manager for database cursors.

    Args:
        commit (bool): Whether to commit the transaction after executing queries.

    Yields:
        psycopg2.extensions.cursor: A database cursor.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            if commit:
                conn.commit()
        finally:
            cursor.close()