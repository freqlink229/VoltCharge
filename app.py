from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
import bcrypt
import sqlite3

app = Flask(__name__)
CORS(app)

app.config["JWT_SECRET_KEY"] = "super-secret-key"
jwt = JWTManager(app)

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect('ev.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        password TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        energy REAL,
        amount REAL,
        duration TEXT
    )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------- DEMO USER ----------
def seed_user():
    conn = sqlite3.connect('ev.db')
    c = conn.cursor()

    hashed = bcrypt.hashpw("1234".encode(), bcrypt.gensalt()).decode()

    try:
        c.execute("INSERT INTO users VALUES (?,?)", ("admin", hashed))
    except:
        pass

    conn.commit()
    conn.close()

seed_user()

# ---------- LOGIN ----------
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = data.get("userId")
    password = data.get("password")

    conn = sqlite3.connect('ev.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE id=?", (user,))
    row = c.fetchone()
    conn.close()

    if row and bcrypt.checkpw(password.encode(), row[0].encode()):
        token = create_access_token(identity=user)
        return jsonify(success=True, token=token)

    return jsonify(success=False), 401

# ---------- LIVE DATA ----------
live_data = {
    "voltage": 0,
    "current": 0,
    "power": 0,
    "energy": 0,
    "bill": 0
}

@app.route('/update-data', methods=['POST'])
def update_data():
    global live_data
    live_data = request.json
    return jsonify(status="ok")

@app.route('/live-data')
@jwt_required()
def get_data():
    return jsonify(live_data)

# ---------- SAVE SESSION ----------
@app.route('/save-session', methods=['POST'])
@jwt_required()
def save_session():
    data = request.json

    conn = sqlite3.connect('ev.db')
    c = conn.cursor()

    c.execute("INSERT INTO sessions (user, energy, amount, duration) VALUES (?,?,?,?)",
              (data["user"], data["energy"], data["amount"], data["duration"]))

    conn.commit()
    conn.close()

    return jsonify(status="saved")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
