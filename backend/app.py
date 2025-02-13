import os
import json
import logging
import hashlib
import itertools
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from cryptography.fernet import Fernet
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from synthetic_data import generate_synthetic_clients  # Ensure this module exists

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
        self.global_model = LinearRegression()
        self.global_model.coef_ = np.zeros(input_dim)
        self.global_model.intercept_ = 0.0

    def aggregate_updates(self):
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

# We'll no longer use a numerical interest mapping in process_user_data.
# interest_map can still be used for other purposes if needed.
interest_map = {"tech": 1, "finance": 2, "sports": 3, "health": 4, "education": 5}

# Serve Static Files
@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory(static_dir, path)

@app.route("/")
def serve_index():
    return render_template("index.html")

@app.route("/dashboard")
def serve_dashboard():
    return render_template("Dashboard.html")

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"), "favicon.ico")

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

def get_recommended_product(seg_mean):
    """
    Return a product recommendation based on the segment's average budget.
    Adjust the thresholds and products as needed.
    """
    if seg_mean >= 800:
        return "Premium Smart TV"
    elif seg_mean >= 600:
        return "High-end Smartphone"
    elif seg_mean >= 400:
        return "Mid-range Laptop"
    else:
        return "Budget Earbuds"

@app.route("/api/segments")
def get_segments():
    try:
        if not user_data:
            return jsonify({"error": "No user data available"}), 400

        decrypted_data = [decrypt_data(data) for data in user_data.values()]
        df = pd.DataFrame(decrypted_data)

        # Detailed statistics for budgets
        avg_budget = float(df["budget"].mean())
        median_budget = float(df["budget"].median())
        std_budget = float(df["budget"].std())
        min_budget = float(df["budget"].min())
        max_budget = float(df["budget"].max())

        # Compute overall common interest across all users:
        # Since interests are now stored as lists, we flatten them.
        all_interests = list(itertools.chain.from_iterable(df["interests"].tolist()))
        common_interest = pd.Series(all_interests).mode()[0] if all_interests else "N/A"

        df_numeric = df[["budget"]].copy()
        # For clustering, we still use a numeric representation for interests.
        # One simple approach is to count the number of interests selected.
        df_numeric["interest_count"] = df["interests"].apply(len)

        if fl_model.global_model:
            df_numeric["prediction"] = fl_model.global_model.predict(df_numeric)
            clusters = KMeans(n_clusters=5, random_state=42).fit_predict(df_numeric)
        else:
            clusters = KMeans(n_clusters=5, random_state=42).fit_predict(df_numeric)

        # Build detailed segment information with product recommendations
        segment_details = []
        unique_segments = np.unique(clusters)
        for seg in unique_segments:
            seg_mask = clusters == seg
            seg_budget = df.loc[seg_mask, "budget"]
            seg_median = seg_budget.median() if not seg_budget.empty else 0
            seg_mean = seg_budget.mean() if not seg_budget.empty else 0
            # For each segment, compute the most common interest.
            seg_interests = list(itertools.chain.from_iterable(df.loc[seg_mask, "interests"].tolist()))
            seg_common_interest = pd.Series(seg_interests).mode()[0] if seg_interests else "N/A"
            recommended_product = get_recommended_product(seg_mean)
            segment_details.append({
                "segmentId": int(seg),
                "description": f"This segment has an average budget of ${seg_mean:.2f} with a median of ${seg_median:.2f}.",
                "preferences": seg_common_interest,  # Most common interest in this segment
                "avgTargetPrice": seg_mean,
                "recommendedProduct": recommended_product
            })

        return jsonify({
            "segments": clusters.tolist(),
            "model_version": fl_model.model_version,
            "participants": len(user_data),
            "stats": {
                "average_budget": avg_budget,
                "median_budget": median_budget,
                "std_budget": std_budget,
                "min_budget": min_budget,
                "max_budget": max_budget,
                "common_interests": common_interest
            },
            "segmentDetails": segment_details
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
    # Store the average budget and the list of interests as given (do not sum interests)
    budget = (float(prefs["budget"][0]) + float(prefs["budget"][1])) / 2
    interests = prefs.get("interests", [])
    return {"budget": budget, "interests": interests}

def process_federated_update(user_id: str, encrypted_data: bytes) -> bool:
    try:
        data = decrypt_data(encrypted_data)
        # For clustering, we still need numeric features.
        # Here we use budget and the number of interests selected.
        features = np.array([data["budget"], len(data["interests"])])
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
