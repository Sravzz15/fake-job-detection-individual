import sqlite3
import os
from flask_bcrypt import Bcrypt
from flask import Flask

app = Flask(__name__)
bcrypt = Bcrypt(app)

DB_PATH = os.path.join(os.path.dirname(__file__), 'job_predictions.db')

def setup_admin():
    # 'admin123' becomes a secure hash
    hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR REPLACE INTO admin (username, password) VALUES (?, ?)", ('admin', hashed_pw))
        conn.commit()
        print("Admin user created successfully (User: admin / Pass: admin123)")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    setup_admin()