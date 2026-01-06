import sqlite3
import os

db_path = 'c:/workspace/agi/memory/experience_vault.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(experiences)")
        columns = [c[1] for c in cursor.fetchall()]
        if 'domain' not in columns:
            cursor.execute("ALTER TABLE experiences ADD COLUMN domain TEXT DEFAULT 'general'")
            conn.commit()
            print("✓ Migration: Added 'domain' column to experience_vault.db")
        else:
            print("- Migration: 'domain' column already exists")
    except Exception as e:
        print(f"✗ Migration failed: {e}")
    finally:
        conn.close()
else:
    print("- Migration: Database file not found, skipping.")
