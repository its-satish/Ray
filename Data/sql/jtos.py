import json
import sqlite3
from sqlite3 import Error
import os

def create_connection():
    """Connect to existing SQLite database in Data folder"""
    try:
        db_path = os.path.join("Data", "db.sqlite")
        conn = sqlite3.connect(db_path)
        return conn
    except Error as e:
        print(f"Database connection error: {e}")
        return None

def verify_table(conn):
    """Verify if chat_history table exists with correct structure"""
    try:
        cursor = conn.cursor()
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_history'")
        if not cursor.fetchone():
            raise Error("chat_history table does not exist")
        
        # Verify columns exist
        cursor.execute("PRAGMA table_info(chat_history)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'role' not in columns or 'content' not in columns:
            raise Error("Table missing required columns")
            
        return True
    except Error as e:
        print(f"Table verification failed: {e}")
        return False

def import_data(conn):
    """Import data from ChatLog.json to SQLite"""
    try:
        json_path = os.path.join("Data", "ChatLog.json")
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cursor = conn.cursor()
        inserted_count = 0
        
        for message in data:
            try:
                cursor.execute("""
                INSERT INTO chat_history (role, content)
                VALUES (?, ?)
                """, (message['role'], message['content']))
                inserted_count += 1
            except sqlite3.IntegrityError:
                print(f"Skipping duplicate message: {message['content'][:50]}...")
                continue
        
        conn.commit()
        print(f"Successfully imported {inserted_count}/{len(data)} messages!")
        return inserted_count
    except Exception as e:
        conn.rollback()
        print(f"Import error: {e}")
        return 0

if __name__ == '__main__':
    # 1. Connect to existing database
    conn = create_connection()
    if not conn:
        exit()
    
    # 2. Verify table structure
    if not verify_table(conn):
        conn.close()
        exit()
    
    # 3. Import data
    import_data(conn)
    
    # 4. Close connection
    conn.close()