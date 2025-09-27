from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

# 🧠 Create database and tables if not exist
def init_db():
    conn = sqlite3.connect('journal.db')
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Journals table linked to users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS journals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            mood INTEGER,
            entry TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# 📝 Signup route
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = sqlite3.connect('journal.db')
    cursor = conn.cursor()
    try:
        hashed_password = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        return jsonify({"message": "Signup successful!"})
    except sqlite3.IntegrityError:
        return jsonify({"message": "Username already exists."}), 409
    finally:
        conn.close()

# 🔐 Login route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = sqlite3.connect('journal.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, password FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[1], password):
        return jsonify({"message": "Login successful!", "user_id": user[0]})
    else:
        return jsonify({"message": "Invalid credentials."}), 401

# ✍️ Submit journal entry (linked to user)
@app.route('/submit_journal', methods=['POST'])
def submit_journal():
    data = request.get_json()
    entry = data.get('entry')
    mood = int(data.get('mood'))
    user_id = int(data.get('user_id'))

    conn = sqlite3.connect('journal.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO journals (user_id, mood, entry) VALUES (?, ?, ?)', (user_id, mood, entry))
    conn.commit()
    conn.close()

    return jsonify({"message": "Journal saved to database!"})

# 📜 Get journal history for a user
@app.route('/get_journals', methods=['POST'])
def get_journals():
    data = request.get_json()
    user_id = int(data.get('user_id'))

    conn = sqlite3.connect('journal.db')
    cursor = conn.cursor()
    cursor.execute('SELECT mood, entry, timestamp FROM journals WHERE user_id = ? ORDER BY timestamp DESC', (user_id,))
    rows = cursor.fetchall()
    conn.close()

    journals = [
        {"mood": row[0], "entry": row[1], "timestamp": row[2]}
        for row in rows
    ]
    return jsonify(journals)

# ✅ Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
