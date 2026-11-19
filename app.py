import os
import random
import string
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ───────── ADMIN CONFIG ─────────
ADMIN_PASSWORD = "SEIJI2009"

# ───────── IN-MEMORY DATABASE ─────────
# Format: "KEY-123": {"status": "active", "features": {...}}
DB_USERS = {
    "SEIJI-TRIAL-123": {
        "status": "active",
        "features": {"kill": True, "gold": True, "drone": True, "bypass": False}
    }
}

# ───────── USER API ─────────
@app.route('/api/config', methods=['GET'])
def get_config():
    key = request.args.get('key')
    if not key or key not in DB_USERS:
        return jsonify({"status": False, "message": "Invalid Key"}), 403
    
    user_data = DB_USERS[key]
    if user_data["status"] != "active":
        return jsonify({"status": False, "message": "Key Revoked"}), 403

    return jsonify({"status": True, "features": user_data["features"]})

@app.route('/api/update', methods=['POST'])
def update_config():
    data = request.json
    key = data.get('key')
    feature = data.get('feature')
    state = data.get('state')
    
    if key in DB_USERS:
        DB_USERS[key]["features"][feature] = state
        return jsonify({"status": True, "message": "Updated"})
    return jsonify({"status": False, "message": "User not found"}), 404

# ───────── ADMIN API ─────────
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    if data.get('password') == ADMIN_PASSWORD:
        return jsonify({"status": True, "token": "admin-session-ok"})
    return jsonify({"status": False, "message": "Wrong Password"}), 401

@app.route('/api/admin/keys', methods=['GET'])
def get_all_keys():
    if request.headers.get('Authorization') != "Bearer admin-session-ok":
        return jsonify({"status": False}), 401
    return jsonify({"status": True, "keys": DB_USERS})

@app.route('/api/admin/create', methods=['POST'])
def create_key():
    if request.headers.get('Authorization') != "Bearer admin-session-ok":
        return jsonify({"status": False}), 401
    
    raw = "".join(random.choices(string.ascii_uppercase + string.digits, k=12))
    new_key = f"SEIJI-{raw[:4]}-{raw[4:8]}-{raw[8:12]}"
    
    DB_USERS[new_key] = {
        "status": "active",
        "features": {"kill": False, "gold": False, "drone": False, "bypass": False}
    }
    return jsonify({"status": True, "key": new_key})

@app.route('/api/admin/edit', methods=['POST'])
def edit_key():
    if request.headers.get('Authorization') != "Bearer admin-session-ok":
        return jsonify({"status": False}), 401
    
    data = request.json
    key = data.get('key')
    feature = data.get('feature')
    state = data.get('state')
    
    if key in DB_USERS:
        DB_USERS[key]["features"][feature] = state
        return jsonify({"status": True})
    return jsonify({"status": False}), 404

@app.route('/api/admin/revoke', methods=['POST'])
def revoke_key():
    if request.headers.get('Authorization') != "Bearer admin-session-ok":
        return jsonify({"status": False}), 401
    
    data = request.json
    key = data.get('key')
    
    if key in DB_USERS:
        del DB_USERS[key]
        return jsonify({"status": True})
    return jsonify({"status": False}), 404

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
