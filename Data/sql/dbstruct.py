import sqlite3
from sqlite3 import Error
import os

def create_connection():
    """Create a database connection to SQLite database"""
    try:
        # Ensure the Data directory exists
        os.makedirs("Data", exist_ok=True)
        
        # Connect to the database (creates it if doesn't exist)
        conn = sqlite3.connect("Data/db.sqlite")
        return conn
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

def print_table_structure():
    """Prints the structure of the chat_history table"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(chat_history)")
            print("\nTable structure:")
            print("-" * 60)
            print(f"{'CID':<4} | {'Name':<12} | {'Type':<10} | {'Notnull':<7} | {'dflt_value':<10} | {'PK':<2}")
            print("-" * 60)
            
            for column in cursor.fetchall():
                print(f"{column[0]:<4} | {column[1]:<12} | {column[2]:<10} | {column[3]:<7} | {str(column[4] or ''):<10} | {column[5]:<2}")
            
            print("-" * 60)
        except Error as e:
            print(f"Error reading table structure: {e}")
        finally:
            conn.close()

# First initialize the database (creates table if needed)
def initialize_database():
    """Initialize the database with required tables and columns"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Create table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    search_query TEXT
                )
            """)
            conn.commit()
        except Error as e:
            print(f"Error initializing database: {e}")
        finally:
            conn.close()

# Run the functions in correct order
initialize_database()
print_table_structure()