from flask import Flask, request, jsonify, send_from_directory
from cryptography.fernet import Fernet
import hashlib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
import json
import os
import logging
from typing import Dict, List
from synthetic_data import generate_synthetic_clients
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.INFO)

# Configuration
FEDERATION_ROUNDS = 5
MIN_CLIENTS_FOR_AGGREGATION = 10
MODEL_VERSION = "1.0"
ANONYMIZATION_SALT = os.getenv("ANONYMIZATION_SALT", "default-secret-salt")  # Change in production!

# Encryption setup
KEY_FILE = "secret.key"
def load_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    else:
        new_key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(new_key)
        return new_key

key = load_key()
cipher = Fernet(key)

# Federated Learning State
class FederatedLearningModel:
    def __init__(self):
        self.global_model = None
        self.client_updates = []
        self.model_version = MODEL_VERSION

    def initialize_global_model(self, input_dim):
        """Initialize a simple linear model for demonstration"""
        self.global_model = LinearRegression()
        self.global_model.coef_ = np.zeros(input_dim)
        self.global_model.intercept_ = 0.0

    def aggregate_updates(self):
        """Federated Averaging implementation"""
        if len(self.client_updates) < MIN_CLIENTS_FOR_AGGREGATION:
            app.logger.warning("Not enough clients for aggregation")
            return False

        avg_coef = np.mean([update['coef'] for update in self.client_updates], axis=0)
        avg_intercept = np.mean([update['intercept'] for update in self.client_updates])

        self.global_model.coef_ = avg_coef
        self.global_model.intercept_ = avg_intercept
        self.client_updates = []
        return True

fl_model = FederatedLearningModel()

# Privacy-preserving user handling
def anonymize_user_id(user_id: str) -> str:
    """Create irreversible hash of user ID for internal use"""
    return hashlib.sha256((user_id + ANONYMIZATION_SALT).encode()).hexdigest()

# In-memory storage with encrypted data
user_data: Dict[str, bytes] = {}  # {anonymized_id: encrypted_data}
clients = generate_synthetic_clients(100)

interest_map = {
    "tech": 1,
    "finance": 2,
    "sports": 3,
    "health": 4,
    "education": 5
}

# Serve static files from React build
# Serve React's static files from the build directory
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('frontend/build/static', path)

# Serve other static files (like manifest.json)
@app.route('/<string:filename>')
def serve_root_files(filename):
    if filename in ['manifest.json', 'logo192.png', 'favicon.ico']:
        return send_from_directory('frontend/build', filename)
    return jsonify({"error": "Not found"}), 404

# Main catch-all route for React's client-side routing
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path and os.path.exists(os.path.join('frontend/build', path)):
        return send_from_directory('frontend/build', path)
    return send_from_directory('frontend/build', 'index.html')

@app.route('/api/save-preferences', methods=['POST'])
def save_preferences():
    """Endpoint for storing encrypted user preferences"""
    raw_user_id = request.headers.get('X-User-ID')
    if not raw_user_id:
        return jsonify({"error": "Missing user ID"}), 400

    # Anonymize user ID immediately
    user_id = anonymize_user_id(raw_user_id)

    data = request.get_json()
    if not data or 'prefs' not in data:
        return jsonify({"error": "Invalid data format"}), 400

    try:
        processed_data = process_user_data(data['prefs'])
        encrypted_data = encrypt_data(processed_data)
        user_data[user_id] = encrypted_data

        if process_federated_update(user_id, encrypted_data):
            return jsonify({"status": "success", "federation": "update_accepted"})
        return jsonify({"status": "success", "federation": "update_queued"})

    except Exception as e:
        app.logger.error(f"Processing failed: {str(e)}")
        return jsonify({"error": "Processing failed"}), 500

@app.route('/api/segments')
def get_segments():
    """Endpoint for getting anonymized market segments"""
    try:
        if not user_data:
            return jsonify({"error": "No user data available"}), 400

        decrypted_data = [decrypt_data(data) for data in user_data.values()]
        df = pd.DataFrame(decrypted_data)
        df_numeric = df[['budget', 'interests']]

        if fl_model.global_model:
            df_numeric['prediction'] = fl_model.global_model.predict(df_numeric)
            clusters = KMeans(n_clusters=5).fit_predict(df_numeric)
        else:
            clusters = KMeans(n_clusters=5).fit_predict(df_numeric[['budget', 'interests']])

        return jsonify({
            "segments": clusters.tolist(),
            "model_version": fl_model.model_version,
            "participants": len(user_data),
            # Return aggregated data only
            "stats": {
                "average_budget": float(df_numeric['budget'].mean()),
                "common_interests": int(df_numeric['interests'].mode()[0])
            }
        })
    except Exception as e:
        app.logger.error(f"Segmentation failed: {str(e)}")
        return jsonify({"error": "Segmentation failed"}), 500

@app.route('/api/model', methods=['GET'])
def get_global_model():
    """Endpoint for model distribution"""
    if not fl_model.global_model:
        return jsonify({"error": "Model not initialized"}), 404

    return jsonify({
        "coef": fl_model.global_model.coef_.tolist(),
        "intercept": fl_model.global_model.intercept_,
        "version": fl_model.model_version
    })

def process_user_data(prefs: dict) -> dict:
    """Convert raw preferences to numerical features"""
    budget = (float(prefs['budget'][0]) + float(prefs['budget'][1])) / 2
    interests = sum(interest_map.get(i, 0) for i in prefs.get('interests', []))
    return {"budget": budget, "interests": interests}

def process_federated_update(user_id: str, encrypted_data: bytes) -> bool:
    """Handle federated learning updates"""
    try:
        data = decrypt_data(encrypted_data)
        features = np.array([data['budget'], data['interests']])

        # Simulated local training
        client_model = LinearRegression()
        X = np.random.rand(10, 2)  # Mock data
        y = np.random.rand(10)
        client_model.fit(X, y)

        fl_model.client_updates.append({
            "coef": client_model.coef_,
            "intercept": client_model.intercept_,
            "user_id": user_id  # Using anonymized ID
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
    """Encrypt data with Fernet"""
    return cipher.encrypt(json.dumps(data).encode())

def decrypt_data(encrypted_data: bytes) -> dict:
    """Decrypt Fernet-encrypted data"""
    return json.loads(cipher.decrypt(encrypted_data).decode())

if __name__ == '__main__':
    fl_model.initialize_global_model(input_dim=2)
    app.run(host='0.0.0.0', port=5001, ssl_context=("cert.pem", "key.pem"))
