from flask import Flask, redirect, request, jsonify, send_from_directory, render_template
from cryptography.fernet import Fernet
import hashlib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
import json
import os
import logging
from synthetic_data import generate_synthetic_clients
from flask_cors import CORS

# Determine the base directory (one level up from backend)
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Set the template and static directories using absolute paths
template_dir = os.path.join(basedir, "templates")
static_dir = os.path.join(basedir, "frontend/build/static")
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
CORS(app)
app.logger.setLevel(logging.INFO)

# Configuration
FEDERATION_ROUNDS = 5
MIN_CLIENTS_FOR_AGGREGATION = 10
MODEL_VERSION = "1.0"
ANONYMIZATION_SALT = os.getenv("ANONYMIZATION_SALT", "default-secret-salt")

# Encryption setup
KEY_FILE = "secret.key"

def load_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    new_key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(new_key)
    return new_key

key = load_key()
cipher = Fernet(key)

# Federated Learning Model
class FederatedLearningModel:
    def __init__(self):
        self.global_model = None
        self.client_updates = []
        self.model_version = MODEL_VERSION

    def initialize_global_model(self, input_dim):
        """Initialize a simple linear model"""
        self.global_model = LinearRegression()
        self.global_model.coef_ = np.zeros(input_dim)
        self.global_model.intercept_ = 0.0

    def aggregate_updates(self):
        """Federated Averaging"""
        if len(self.client_updates) < MIN_CLIENTS_FOR_AGGREGATION:
            app.logger.warning("Not enough clients for aggregation")
            return False

        avg_coef = np.mean([update["coef"] for update in self.client_updates], axis=0)
        avg_intercept = np.mean([update["intercept"] for update in self.client_updates])

        self.global_model.coef_ = avg_coef
        self.global_model.intercept_ = avg_intercept
        self.client_updates = []
        return True

fl_model = FederatedLearningModel()

def anonymize_user_id(user_id: str) -> str:
    return hashlib.sha256((user_id + ANONYMIZATION_SALT).encode()).hexdigest()

user_data = {}
clients = generate_synthetic_clients(100)

interest_map = {
    "tech": 1,
    "finance": 2,
    "sports": 3,
    "health": 4,
    "education": 5,
}

# Serve Static Files
@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory("frontend/build/static", path)

@app.route("/")
def serve_index():
    try:
        return render_template("index.html")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"), "favicon.ico")

@app.route("/dashboard")
def serve_dashboard():
    try:
        return render_template("Dashboard.html")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API Routes
@app.route("/api/save-preferences", methods=["POST"])
def save_preferences():
    raw_user_id = request.headers.get("X-User-ID")
    if not raw_user_id:
        return jsonify({"error": "Missing user ID"}), 400

    user_id = anonymize_user_id(raw_user_id)
    data = request.get_json()
    if not data or "prefs" not in data:
        return jsonify({"error": "Invalid data format"}), 400

    try:
        processed_data = process_user_data(data["prefs"])
        encrypted_data = encrypt_data(processed_data)
        user_data[user_id] = encrypted_data

        if process_federated_update(user_id, encrypted_data):
            return jsonify({"status": "success", "federation": "update_accepted"})
        return jsonify({"status": "success", "federation": "update_queued"})

    except Exception as e:
        app.logger.error(f"Processing failed: {str(e)}")
        return jsonify({"error": "Processing failed"}), 500

@app.route("/api/segments")
def get_segments():
    try:
        if not user_data:
            return jsonify({"error": "No user data available"}), 400

        decrypted_data = [decrypt_data(data) for data in user_data.values()]
        df = pd.DataFrame(decrypted_data)
        df_numeric = df[["budget", "interests"]]

        if fl_model.global_model:
            df_numeric["prediction"] = fl_model.global_model.predict(df_numeric)
            clusters = KMeans(n_clusters=5).fit_predict(df_numeric)
        else:
            clusters = KMeans(n_clusters=5).fit_predict(df_numeric[["budget", "interests"]])

        return jsonify({
            "segments": clusters.tolist(),
            "model_version": fl_model.model_version,
            "participants": len(user_data),
            "stats": {
                "average_budget": float(df_numeric["budget"].mean()),
                "common_interests": int(df_numeric["interests"].mode()[0]),
            },
        })
    except Exception as e:
        app.logger.error(f"Segmentation failed: {str(e)}")
        return jsonify({"error": "Segmentation failed"}), 500

@app.route("/api/model", methods=["GET"])
def get_global_model():
    if not fl_model.global_model:
        return jsonify({"error": "Model not initialized"}), 404

    return jsonify({
        "coef": fl_model.global_model.coef_.tolist(),
        "intercept": fl_model.global_model.intercept_,
        "version": fl_model.model_version,
    })

def process_user_data(prefs: dict) -> dict:
    budget = (float(prefs["budget"][0]) + float(prefs["budget"][1])) / 2
    interests = sum(interest_map.get(i, 0) for i in prefs.get("interests", []))
    return {"budget": budget, "interests": interests}

def process_federated_update(user_id: str, encrypted_data: bytes) -> bool:
    try:
        data = decrypt_data(encrypted_data)
        features = np.array([data["budget"], data["interests"]])

        client_model = LinearRegression()
        X = np.random.rand(10, 2)
        y = np.random.rand(10)
        client_model.fit(X, y)

        fl_model.client_updates.append({
            "coef": client_model.coef_,
            "intercept": client_model.intercept_,
            "user_id": user_id,
        })

        if len(fl_model.client_updates) >= MIN_CLIENTS_FOR_AGGREGATION:
            fl_model.aggregate_updates()
            fl_model.model_version = f"{MODEL_VERSION}.{len(fl_model.client_updates)}"
            return True
        return False
    except Exception as e:
        app.logger.error(f"Federated update failed: {str(e)}")
        return False

def encrypt_data(data: dict) -> bytes:
    return cipher.encrypt(json.dumps(data).encode())

def decrypt_data(encrypted_data: bytes) -> dict:
    return json.loads(cipher.decrypt(encrypted_data).decode())

if __name__ == "__main__":
    fl_model.initialize_global_model(input_dim=2)
    app.run(host="0.0.0.0", port=5001, debug=True)
