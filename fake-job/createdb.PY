import sqlite3
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, "job_predictions.db")

def create_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Predictions Table (Stores every scan)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_description TEXT,
        prediction TEXT,
        confidence REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        flagged TEXT DEFAULT 'No'
    )
    """)
    
    # 2. Admin Table (Stores credentials)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # 3. Retrain Logs Table (For Milestone 4: Retraining Workflow)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS retrain_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        accuracy REAL,
        record_count INTEGER,
        training_source TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    print(f"Database schema initialized at: {DB_PATH}")

if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH) # Start fresh to ensure schema matches
    create_table()