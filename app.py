import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Simple DB
DB_USERS = {
    "SEIJI-TRIAL-123": {
        "status": "active",
        "features": {"kill": True, "gold": True, "drone": True, "bypass": False}
    },
    "SEIJI-VIP-999": {
        "status": "active",
        "features": {"kill": True, "gold": True, "drone": True, "bypass": True}
    }
}

@app.route('/api/config', methods=['GET'])
def get_config():
    key = request.args.get('key')
    if not key or key not in DB_USERS:
        return jsonify({"status": False, "message": "Invalid Key"}), 403
    
    user_data = DB_USERS[key]
    if user_data["status"] != "active":
        return jsonify({"status": False, "message": "Key Expired"}), 403

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

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
