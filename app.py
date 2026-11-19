import os
import random
import string
import sqlite3
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ADMIN_PASSWORD = "BEGIE"
DB_FILE = "licenses.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # status: 1 = Active, 0 = Disabled
    c.execute('''CREATE TABLE IF NOT EXISTS keys
                 (key TEXT PRIMARY KEY, status INTEGER DEFAULT 1)''')
    conn.commit()
    conn.close()

init_db()

def db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ───────── USER API ─────────
@app.route('/api/auth', methods=['GET'])
def auth():
    key = request.args.get('key', '').strip()
    if not key:
        return jsonify({"status": False, "msg": "No key provided"}), 400
    
    conn = db()
    row = conn.execute("SELECT status FROM keys WHERE key=?", (key,)).fetchone()
    conn.close()

    if row and row['status'] == 1:
        return jsonify({"status": True})
    return jsonify({"status": False, "msg": "Invalid or Disabled"}), 403

# ───────── ADMIN API ─────────
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    if request.json.get('password') == ADMIN_PASSWORD:
        return jsonify({"status": True, "token": "admin-ok"})
    return jsonify({"status": False}), 401

@app.route('/api/admin/keys', methods=['GET'])
def get_keys():
    if request.headers.get('Authorization') != "Bearer admin-ok":
        return jsonify({"status": False}), 401
    conn = db()
    rows = conn.execute("SELECT * FROM keys").fetchall()
    conn.close()
    return jsonify({"status": True, "keys": [dict(r) for r in rows]})

@app.route('/api/admin/create', methods=['POST'])
def create_key():
    if request.headers.get('Authorization') != "Bearer admin-ok":
        return jsonify({"status": False}), 401
    
    raw = "".join(random.choices(string.ascii_uppercase + string.digits, k=12))
    new_key = f"SEIJI-{raw[:4]}-{raw[4:8]}-{raw[8:12]}"
    
    conn = db()
    try:
        conn.execute("INSERT INTO keys (key, status) VALUES (?, 1)", (new_key,))
        conn.commit()
        return jsonify({"status": True, "key": new_key})
    except sqlite3.IntegrityError:
        return jsonify({"status": False, "msg": "Key collision"}), 500
    finally:
        conn.close()

@app.route('/api/admin/toggle', methods=['POST'])
def toggle_key():
    if request.headers.get('Authorization') != "Bearer admin-ok":
        return jsonify({"status": False}), 401
    
    data = request.json
    key = data.get('key')
    
    conn = db()
    row = conn.execute("SELECT status FROM keys WHERE key=?", (key,)).fetchone()
    if row:
        new_status = 0 if row['status'] == 1 else 1
        conn.execute("UPDATE keys SET status=? WHERE key=?", (new_status, key))
        conn.commit()
        conn.close()
        return jsonify({"status": True, "new_status": new_status})
    conn.close()
    return jsonify({"status": False}), 404

@app.route('/api/admin/delete', methods=['POST'])
def delete_key():
    if request.headers.get('Authorization') != "Bearer admin-ok":
        return jsonify({"status": False}), 401
    
    key = request.json.get('key')
    conn = db()
    conn.execute("DELETE FROM keys WHERE key=?", (key,))
    conn.commit()
    conn.close()
    return jsonify({"status": True})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
