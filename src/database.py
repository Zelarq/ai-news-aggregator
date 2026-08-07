import sqlite3
import datetime
from src.config import Config

def get_db_connection(db_path=None):
    """Returns a connection to the SQLite database."""
    if db_path is None:
        db_path = Config.DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return rows as dictionary-like objects
    return conn

def init_db(db_path=None):
    """Initializes the database and creates the schema if it does not exist."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raw_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        external_id TEXT UNIQUE,
        source TEXT,
        title TEXT,
        content TEXT,
        url TEXT,
        published_at TEXT,
        collected_at TEXT,
        status TEXT DEFAULT 'new',
        summary TEXT,
        category TEXT
    )
    """)
    conn.commit()
    conn.close()

def save_raw_item(item_data, db_path=None):
    """
    Saves a raw collected item into the database.
    Ignores duplicates based on the UNIQUE external_id constraint.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    collected_at = datetime.datetime.utcnow().isoformat()
    try:
        cursor.execute("""
        INSERT OR IGNORE INTO raw_items (
            external_id, source, title, content, url, published_at, collected_at, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'new')
        """, (
            item_data['external_id'],
            item_data['source'],
            item_data['title'],
            item_data['content'],
            item_data['url'],
            item_data['published_at'],
            collected_at
        ))
        conn.commit()
        # Returns True if a new row was inserted, False if ignored
        is_new = cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error during insert: {e}")
        is_new = False
    finally:
        conn.close()
    return is_new

def get_unsummarized_items(db_path=None):
    """Retrieves all items that are newly collected and need summarization."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, external_id, source, title, content, url, published_at 
    FROM raw_items 
    WHERE status = 'new'
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_item_summary(external_id, summary, category, db_path=None):
    """Updates the summary, category, and sets status to 'summarized'."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
        UPDATE raw_items
        SET summary = ?, category = ?, status = 'summarized'
        WHERE external_id = ?
        """, (summary, category, external_id))
        conn.commit()
        success = cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error during update: {e}")
        success = False
    finally:
        conn.close()
    return success

def get_summarized_unsent_items(db_path=None):
    """Retrieves all items that have been summarized but not yet emailed."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, external_id, source, title, url, summary, category, published_at 
    FROM raw_items 
    WHERE status = 'summarized'
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def mark_items_as_sent(external_ids, db_path=None):
    """Marks a list of item IDs as 'sent'."""
    if not external_ids:
        return
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in external_ids)
    try:
        cursor.execute(f"""
        UPDATE raw_items
        SET status = 'sent'
        WHERE external_id IN ({placeholders})
        """, external_ids)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error during status update: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Test DB initialisation
    init_db("test_digest.db")
    print("Database initialisation test successful.")
