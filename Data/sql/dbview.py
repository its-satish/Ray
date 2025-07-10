import sqlite3
from tabulate import tabulate

def view_database():
    # Connect to the database
    conn = sqlite3.connect('Data/db.sqlite')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("\nAvailable Tables:")
    for table in tables:
        print(f"- {table[0]}")
    
    # View chat_history table
    print("\nChat History:")
    cursor.execute("SELECT * FROM chat_history")
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
    
    print(tabulate(rows, headers=columns, tablefmt="grid"))
    
    # Close connection
    conn.close()

if __name__ == "__main__":
    view_database()