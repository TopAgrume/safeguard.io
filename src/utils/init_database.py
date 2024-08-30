import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def init_database():
    """
    Initializes the PostgreSQL database by creating the necessary tables if they don't exist.

    This function connects to the PostgreSQL server using the provided connection parameters,
    creates tables for users, contacts, daily messages, contact requests, pending requests,
    bug reports, and a check queue. The function sets the isolation level to AUTOCOMMIT to
    ensure that the table creation statements are executed immediately.

    Tables:
        - users: Stores user information such as username, alert mode, and response status.
        - contacts: Manages user contacts and pairing status.
        - daily_messages: Stores scheduled daily messages for users.
        - contact_requests: Manages contact requests between users.
        - pending_requests: Handles pending contact requests.
        - bug_reports: Logs bug reports submitted by users.
        - check_queue: Manages verification checks and reminders.

    The function prints a success message after creating the tables and closes the database connection.
    """
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
        state TEXT DEFAULT ''
    );
    
    CREATE TABLE IF NOT EXISTS contacts (
        id SERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
        contact_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
        tag VARCHAR(255),
        pair BOOLEAN DEFAULT FALSE,
        UNIQUE (user_id, contact_id, tag)
    );
    
    CREATE TABLE IF NOT EXISTS daily_messages (
        id SERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
        time TIME,
        description TEXT,
        active BOOLEAN
    );
    
    CREATE TABLE IF NOT EXISTS contact_requests (
        user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
        requester_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
        requester_tag VARCHAR(255),
        PRIMARY KEY (user_id, requester_id)
    );
    
    CREATE TABLE IF NOT EXISTS pending_requests (
        requester_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
        target_username VARCHAR(255),
        tag VARCHAR(255),
        PRIMARY KEY (requester_id, target_username),
        UNIQUE (requester_id, target_username, tag)
    );
    
    CREATE TABLE IF NOT EXISTS bug_reports (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        username VARCHAR(255),
        content TEXT,
        reported_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS check_queue (
        id SERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
        time TIME NOT NULL,
        description TEXT NOT NULL,
        reminder_count INT DEFAULT 0,
        waiting_time INT NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """)

    print("Table 'users' created successfully (if it didn't exist).")

    # Close communication with the database
    cur.close()
    conn.close()