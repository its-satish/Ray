import sqlite3
from sqlite3 import Error

def create_connection():
    """Create a database connection to SQLite database"""
    conn = None
    try:
        conn = sqlite3.connect("Data/db.sqlite")
        return conn
    except Error as e:
        print(f"Error connecting to database: {e}")
    return conn

def initialize_database():
    """Initialize the database with required tables and columns"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Create table if it doesn't exist
            # cursor.execute("""
            #     CREATE TABLE IF NOT EXISTS chat_history (
            #         id INTEGER PRIMARY KEY AUTOINCREMENT,
            #         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            #         role TEXT NOT NULL,
            #         content TEXT NOT NULL
            #     )
            # """)

            # cursor.execute("""
            #     DELETE from chat_history where id > '1'
                
            # """)
            
            # Add the search_query column if it doesn't exist
            cursor.execute("PRAGMA table_info(chat_history)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'search_query' not in columns:
                cursor.execute("ALTER TABLE chat_history ADD COLUMN search_query TEXT")
            
            conn.commit()
            print("Database initialized successfully")
            
        except Error as e:
            print(f"Error initializing database: {e}")
        finally:
            if conn:
                conn.close()

# Call this when your application starts
initialize_database()