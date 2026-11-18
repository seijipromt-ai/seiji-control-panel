import os
import sqlite3
import secrets
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "klen_super_secret_2026"

DB_FILE = "keys.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS keys 
                 (key TEXT PRIMARY KEY, expiry TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT)''')
    
    # Default Admin
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES ('admin', 'klen123')")
    conn.commit()
    conn.close()

init_db()

# --- DASHBOARD ROUTES ---
@app.route("/")
def index():
    if "user" not in session: return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        if c.fetchone():
            session["user"] = u
            return redirect(url_for("index"))
        conn.close()
        return "Invalid credentials", 401
    return '''
        <body style="background:#111;color:#fff;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;">
            <form method="POST" style="background:#222;padding:30px;border-radius:10px;">
                <h2 style="margin-top:0;">Admin Login</h2>
                <input type="text" name="username" placeholder="Username" style="display:block;margin-bottom:10px;padding:8px;width:100%;"><br>
                <input type="password" name="password" placeholder="Password" style="display:block;margin-bottom:10px;padding:8px;width:100%;"><br>
                <button type="submit" style="width:100%;padding:10px;background:#E88235;border:none;color:#fff;font-weight:bold;cursor:pointer;">Login</button>
            </form>
        </body>
    '''

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# --- API ROUTES ---
@app.route("/api/generate", methods=["POST"])
def generate():
    if "user" not in session: return jsonify({"err": "Unauthorized"}), 401
    days = int(request.json.get("days", 30))
    expiry = (datetime.now() + timedelta(seconds=60)).strftime("%Y-%m-%d")
    new_key = "SEIJI-" + secrets.token_hex(4).upper() + "-" + secrets.token_hex(4).upper()
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO keys VALUES (?, ?, ?)", (new_key, expiry, "active"))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "key": new_key, "expiry": expiry})

@app.route("/api/keys", methods=["GET"])
def list_keys():
    if "user" not in session: return jsonify({"err": "Unauthorized"}), 401
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM keys")
    keys = [{"key": r[0], "expiry": r[1], "status": r[2]} for r in c.fetchall()]
    conn.close()
    return jsonify(keys)

@app.route("/api/delete/<key>", methods=["DELETE"])
def delete_key(key):
    if "user" not in session: return jsonify({"err": "Unauthorized"}), 401
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM keys WHERE key=?", (key,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

# --- LUA API ENDPOINT ---
@app.route("/api/validate/<key>", methods=["GET"])
def validate_key(key):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM keys WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"valid": False, "msg": "Key not found"})
    
    k, expiry_str, status = row
    if status != "active":
        return jsonify({"valid": False, "msg": "Key disabled"})
        
    expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")
    if datetime.now() > expiry_date:
        return jsonify({"valid": False, "msg": "Key expired"})
        
    return jsonify({"valid": True, "msg": "Access granted", "expiry": expiry_str})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
