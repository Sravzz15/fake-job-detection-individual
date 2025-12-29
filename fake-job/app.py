import os, sqlite3, re, joblib, nltk
import numpy as np
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_bcrypt import Bcrypt
from datetime import datetime
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

app = Flask(__name__)
app.secret_key = "nlp_job_secret_key"
bcrypt = Bcrypt(app)

# Resource Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(BASE_DIR, 'fake_job_model.pkl')
VECTORIZER_FILE = os.path.join(BASE_DIR, 'tfidf_vectorizer.pkl')
DB_PATH = os.path.join(BASE_DIR, "job_predictions.db")

# Load AI Model
def load_resources():
    if os.path.exists(MODEL_FILE) and os.path.exists(VECTORIZER_FILE):
        return joblib.load(MODEL_FILE), joblib.load(VECTORIZER_FILE)
    return None, None

model, vectorizer = load_resources()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def clean_text(text):
    text = re.sub(r'[^a-zA-Z\s]', '', str(text).lower())
    stop_words = set(stopwords.words('english'))
    lem = WordNetLemmatizer()
    return " ".join([lem.lemmatize(w) for w in text.split() if w not in stop_words])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if not model: return jsonify({'error': 'AI Model not loaded'}), 503
    
    raw_text = request.json.get('text', '')
    cleaned = clean_text(raw_text)
    vec = vectorizer.transform([cleaned])
    
    prediction = model.predict(vec)[0]
    confidence = round(np.max(model.predict_proba(vec)) * 100, 2)
    result = "Fake Job" if prediction == 1 else "Real Job"

    # Save to DB (Milestone 4)
    conn = get_db()
    conn.execute("INSERT INTO predictions (job_description, prediction, confidence) VALUES (?, ?, ?)",
                 (raw_text[:500], result, confidence))
    conn.commit()
    conn.close()

    return jsonify({'prediction': result, 'confidence': confidence})

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        conn = get_db()
        admin = conn.execute("SELECT * FROM admin WHERE username=?", (user,)).fetchone()
        if admin and bcrypt.check_password_hash(admin['password'], pw):
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('logged_in'): return redirect(url_for('admin_login'))
    conn = get_db()
    data = {
        'total': conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0],
        'fake': conn.execute("SELECT COUNT(*) FROM predictions WHERE prediction='Fake Job'").fetchone()[0],
        'real': conn.execute("SELECT COUNT(*) FROM predictions WHERE prediction='Real Job'").fetchone()[0],
        'logs': conn.execute("SELECT * FROM retrain_logs ORDER BY id DESC").fetchall()
    }
    return render_template('admin_dashboard.html', **data)
# 1. EXPORT ROUTE (Required by Milestone 4)
@app.route('/export_logs')
def export_logs():
    if not session.get('logged_in'): return redirect(url_for('admin_login'))
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM predictions")
    rows = cursor.fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Description', 'Prediction', 'Confidence', 'Date'])
    for r in rows:
        writer.writerow([r['id'], r['job_description'][:50], r['prediction'], r['confidence'], r['timestamp']])
    
    return Response(output.getvalue(), mimetype="text/csv", 
                    headers={"Content-disposition": "attachment; filename=results.csv"})

# 2. RETRAIN ROUTE (Required by Milestone 4)
@app.route('/retrain_model', methods=['POST'])
def retrain_model_route():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    try:
        # This calls your existing train_model.py script
        import subprocess
        subprocess.run(['python', 'train_model.py'], check=True)
        return jsonify({'message': 'Model successfully updated!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)