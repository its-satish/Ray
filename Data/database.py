import sqlite3
import datetime
from typing import List, Tuple, Optional, Dict
import json
import threading
import sys
import os

class EnhancedDatabase:
    def __init__(self, db_path: str = "Data/assistant.db"):
        self.db_path = db_path
        self.local = threading.local()
        self.init_database()

    def get_connection(self):
        """Get thread-local database connection"""
        if not hasattr(self.local, 'connection'):
            self.local.connection = sqlite3.connect(self.db_path)
            self.local.connection.row_factory = sqlite3.Row
        return self.local.connection
    
    def column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in cursor.fetchall()]
        return column_name in columns

    def init_database(self):
        """Initialize enhanced database schema with migration support"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create messages table with backward compatibility
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                message_type TEXT DEFAULT 'text',
                metadata TEXT,
                search_query TEXT,
                response_type TEXT,
                is_processed BOOLEAN DEFAULT FALSE,
                is_error BOOLEAN DEFAULT FALSE,
                parent_message_id INTEGER,
                FOREIGN KEY (parent_message_id) REFERENCES messages (id)
            )
        ''')
        
        # Check if content_hash column exists, if not add it
        cursor.execute("PRAGMA table_info(messages)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'content_hash' not in columns:
            try:
                cursor.execute('ALTER TABLE messages ADD COLUMN content_hash TEXT')
                conn.commit()
                print("Added content_hash column to messages table")
            except sqlite3.OperationalError as e:
                print(f"Could not add content_hash column: {e}")
        
        # Other tables remain the same...
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                preference_key TEXT,
                preference_value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                task_type TEXT,
                task_content TEXT,
                status TEXT DEFAULT 'pending',
                result TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                error_message TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                title TEXT,
                content TEXT,
                scheduled_time DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                reminder_type TEXT DEFAULT 'once'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                results TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                source TEXT
            )
        ''')
        
        # Create search_cache table for caching search results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_hash TEXT UNIQUE,
                query TEXT,
                results TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                source TEXT,
                cache_duration INTEGER DEFAULT 30
            )
        ''')
        
        # Create indexes safely
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_processed ON messages(is_processed)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_search_cache_query ON search_cache(query_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_search_cache_timestamp ON search_cache(timestamp)')
        
        # Only create content_hash index if column exists
        if 'content_hash' in columns or self.column_exists('messages', 'content_hash'):
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_content_hash ON messages(content_hash)')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_history_status ON task_history(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_scheduled ON reminders(scheduled_time)')
        
        conn.commit()

    def add_message(self, role: str = None, content: str = None, conversation_id: str = None, 
               message_type: str = 'text', metadata: Dict = None, 
               search_query: str = None, response_type: str = None,
               is_processed: bool = False, is_error: bool = False, 
               parent_message_id: int = None, sender: str = None, message: str = None,
               timestamp: str = None) -> int:
        """Add a message with basic duplicate prevention - supports both old and new parameter formats"""
        conn = self.get_connection()
        cursor = conn.cursor()
    
    # Handle backward compatibility - map UI parameters to database parameters
        if sender and not role:
            role = 'user' if sender.lower() == 'user' else 'assistant'
        if message and not content:
            content = message
    
    # Ensure we have required parameters
        if not role or not content:
            print("Error: role and content are required parameters")
            return None
    
        if conversation_id is None:
            conversation_id = f"conv_{int(datetime.datetime.now().timestamp())}"
    
        try:
        # Check for recent duplicate (same content in last 5 messages)
            cursor.execute('''
            SELECT COUNT(*) FROM messages 
            WHERE conversation_id = ? 
            AND role = ? 
            AND content = ? 
            AND datetime(timestamp) > datetime('now', '-1 minute')
            ''', (conversation_id, role, content))
        
            if cursor.fetchone()[0] > 0:
                print(f"Duplicate message prevented: {content[:50]}...")
                return None
        
            cursor.execute('''
            INSERT INTO messages 
            (conversation_id, role, content, message_type, metadata, search_query, 
             response_type, is_processed, is_error, parent_message_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (conversation_id, role, content, message_type, 
                json.dumps(metadata) if metadata else None,
                search_query, response_type, is_processed, is_error, parent_message_id))
        
            message_id = cursor.lastrowid
        
        # If content_hash column exists, update it
            if self.column_exists('messages', 'content_hash'):
                cursor.execute('''
                UPDATE messages 
                SET content_hash = ? 
                WHERE id = ?
                ''', (f"{hash(content)}_{message_id}", message_id))
        
            conn.commit()
        
        # Update conversation timestamp
            self.update_conversation(conversation_id)
        
            return message_id
        
        except Exception as e:
            print(f"Error adding message: {e}")
            return None

    def get_recent_message(self, limit: int = 10, conversation_id: str = None) -> List[Dict]:
        """Get recent messages for UI display - compatible with existing UI code"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if conversation_id:
                cursor.execute('''
                    SELECT id, conversation_id, role, content, timestamp
                    FROM messages
                    WHERE conversation_id = ?
                    AND is_error = FALSE
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (conversation_id, limit))
            else:
                cursor.execute('''
                    SELECT id, conversation_id, role, content, timestamp
                    FROM messages
                    WHERE is_error = FALSE
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
            
            messages = []
            for row in cursor.fetchall():
                # Convert to format expected by UI
                timestamp_str = row[4]
                if isinstance(timestamp_str, str):
                    # Parse timestamp string to datetime, then to unix timestamp
                    try:
                        dt = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        timestamp = dt.timestamp()
                    except:
                        timestamp = datetime.datetime.now().timestamp()
                else:
                    timestamp = timestamp_str
                
                # Map role to sender name for UI compatibility
                sender = "User" if row[2] == 'user' else "Assistant"
                
                messages.append({
                    'id': row[0],
                    'conversation_id': row[1],
                    'sender': sender,  # UI expects 'sender' field
                    'message': row[3],  # UI expects 'message' field
                    'timestamp': timestamp,
                    'role': row[2]  # Keep original role too
                })
            
            return list(reversed(messages))  # Return in chronological order
            
        except Exception as e:
            print(f"Error getting recent messages: {e}")
            return []

    def get_unprocessed_messages(self, conversation_id: str = None, limit: int = 10) -> List[Dict]:
        """Get unprocessed user messages only - with strict filtering"""
        conn = self.get_connection()
        cursor = conn.cursor()
    
        base_query = '''
            SELECT DISTINCT id, conversation_id, role, content, timestamp 
            FROM messages
            WHERE is_processed = FALSE 
            AND role = 'user'
            AND is_error = FALSE
        '''
        
        if conversation_id:
            cursor.execute(base_query + '''
                AND conversation_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
            ''', (conversation_id, limit))
        else:
            cursor.execute(base_query + '''
                ORDER BY timestamp ASC
                LIMIT ?
            ''', (limit,))
    
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'id': row[0],
                'conversation_id': row[1],
                'role': row[2],
                'content': row[3],
                'timestamp': row[4]
            })
    
        return messages

    def mark_as_processed(self, message_id: int) -> bool:
        """Mark a message as processed with verification"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if message exists and is not already processed
        cursor.execute('''
            SELECT is_processed FROM messages WHERE id = ?
        ''', (message_id,))
        
        result = cursor.fetchone()
        if not result:
            return False
            
        if result[0]:  # Already processed
            return True
            
        cursor.execute('''
            UPDATE messages SET is_processed = TRUE WHERE id = ?
        ''', (message_id,))
        
        conn.commit()
        return cursor.rowcount > 0

    def get_conversation_context(self, conversation_id: str, limit: int = 5) -> List[Tuple]:
        """Get recent conversation context - processed messages only"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT role, content FROM messages
            WHERE conversation_id = ? 
            AND is_processed = TRUE
            AND is_error = FALSE
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (conversation_id, limit))
        
        results = cursor.fetchall()
        return [(row[0], row[1]) for row in reversed(results)]

    def create_conversation(self, conversation_id: str = None, title: str = None, 
                          user_id: str = None) -> str:
        """Create a new conversation"""
        if not conversation_id:
            conversation_id = f"conv_{int(datetime.datetime.now().timestamp())}"
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO conversations (id, title, user_id)
            VALUES (?, ?, ?)
        ''', (conversation_id, title, user_id))
        
        conn.commit()
        return conversation_id

    def update_conversation(self, conversation_id: str, title: str = None):
        """Update conversation metadata"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if title:
            cursor.execute('''
                UPDATE conversations 
                SET title = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (title, conversation_id))
        else:
            cursor.execute('''
                UPDATE conversations 
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (conversation_id,))
        
        conn.commit()

    def get_conversation_messages(self, conversation_id: str) -> List[Dict]:
        """Retrieve all messages for a conversation - ordered and clean"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, conversation_id, role, content, timestamp, metadata, is_processed
                FROM messages 
                WHERE conversation_id = ?
                AND is_error = FALSE
                ORDER BY timestamp ASC, id ASC
            ''', (conversation_id,))
        
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'id': row[0],
                    'conversation_id': row[1],
                    'role': row[2],
                    'content': row[3],
                    'timestamp': row[4],
                    'metadata': json.loads(row[5]) if row[5] else {},
                    'is_processed': row[6]
                })
            return messages
        
        except Exception as e:
            print(f"Error retrieving conversation messages: {e}")
            return []

    def cleanup_duplicate_responses(self, conversation_id: str = None):
        """Clean up any duplicate assistant responses"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if conversation_id:
            cursor.execute('''
                DELETE FROM messages 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM messages 
                    WHERE conversation_id = ? AND role = 'assistant'
                    GROUP BY content, parent_message_id
                )
                AND conversation_id = ? AND role = 'assistant'
            ''', (conversation_id, conversation_id))
        else:
            cursor.execute('''
                DELETE FROM messages 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM messages 
                    WHERE role = 'assistant'
                    GROUP BY content, parent_message_id, conversation_id
                )
                AND role = 'assistant'
            ''')
        
        conn.commit()
        return cursor.rowcount

    def get_processing_stats(self) -> Dict:
        """Get processing statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_messages,
                COUNT(CASE WHEN is_processed = TRUE THEN 1 END) as processed_messages,
                COUNT(CASE WHEN is_processed = FALSE AND role = 'user' THEN 1 END) as pending_user_messages,
                COUNT(CASE WHEN role = 'user' THEN 1 END) as total_user_messages,
                COUNT(CASE WHEN role = 'assistant' THEN 1 END) as total_assistant_messages
            FROM messages
            WHERE is_error = FALSE
        ''')
        
        result = cursor.fetchone()
        return {
            'total_messages': result[0],
            'processed_messages': result[1],
            'pending_user_messages': result[2],
            'total_user_messages': result[3],
            'total_assistant_messages': result[4]
        }

    # ===== SEARCH CACHE METHODS =====
    
    def get_search_cache(self, query: str, cache_duration_minutes: int = 30) -> Optional[Dict]:
        """Get cached search results if they exist and are not expired"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create a hash of the query for consistent lookups
            query_hash = str(hash(query.lower().strip()))
            
            # Check for cached results within the cache duration
            cursor.execute('''
                SELECT query, results, timestamp, source
                FROM search_cache
                WHERE query_hash = ?
                AND datetime(timestamp) > datetime('now', '-{} minutes')
                ORDER BY timestamp DESC
                LIMIT 1
            '''.format(cache_duration_minutes), (query_hash,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'query': result[0],
                    'results': json.loads(result[1]) if result[1] else [],
                    'timestamp': result[2],
                    'source': result[3]
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting search cache: {e}")
            return None

    def save_search_result(self, query: str, results: Dict, source: str = 'google') -> bool:
        """Save search results to cache"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create a hash of the query for consistent lookups
            query_hash = str(hash(query.lower().strip()))
            
            # Insert or replace the cached result
            cursor.execute('''
                INSERT OR REPLACE INTO search_cache (query_hash, query, results, source)
                VALUES (?, ?, ?, ?)
            ''', (query_hash, query, json.dumps(results), source))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error saving search result: {e}")
            return False

    def clear_expired_cache(self, cache_duration_minutes: int = 30) -> int:
        """Clear expired cache entries"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM search_cache
                WHERE datetime(timestamp) <= datetime('now', '-{} minutes')
            '''.format(cache_duration_minutes))
            
            removed_count = cursor.rowcount
            conn.commit()
            return removed_count
            
        except Exception as e:
            print(f"Error clearing expired cache: {e}")
            return 0

    def get_search_stats(self) -> Dict:
        """Get search cache statistics"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_cached,
                    COUNT(CASE WHEN datetime(timestamp) > datetime('now', '-30 minutes') THEN 1 END) as fresh_cache,
                    MIN(timestamp) as oldest_entry,
                    MAX(timestamp) as newest_entry
                FROM search_cache
            ''')
            
            result = cursor.fetchone()
            return {
                'total_cached': result[0],
                'fresh_cache': result[1],
                'oldest_entry': result[2],
                'newest_entry': result[3]
            }
            
        except Exception as e:
            print(f"Error getting search stats: {e}")
            return {}

    # ===== OTHER METHODS =====
    
    def add_task(self, conversation_id: str, task_type: str, task_content: str) -> int:
        """Add a task to the task history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO task_history (conversation_id, task_type, task_content)
            VALUES (?, ?, ?)
        ''', (conversation_id, task_type, task_content))
        
        task_id = cursor.lastrowid
        conn.commit()
        return task_id

    def update_task(self, task_id: int, status: str, result: str = None, 
                   error_message: str = None):
        """Update task status and result"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE task_history 
            SET status = ?, result = ?, error_message = ?, 
                completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, result, error_message, task_id))
        
        conn.commit()

    def close(self):
        """Close database connections"""
        if hasattr(self.local, 'connection'):
            self.local.connection.close()

# Global database instance
db = EnhancedDatabase()