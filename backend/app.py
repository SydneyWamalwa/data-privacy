from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
import json
import os
from synthetic_data import generate_synthetic_clients

app = Flask(__name__)

# Use a persistent key so that data remains decryptable across restarts.
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

# In-memory storage for demonstration
user_data = {}
clients = generate_synthetic_clients(100)

# A dictionary to map interests to numerical values
interest_map = {
    "tech": 1,
    "finance": 2,
    "sports": 3,
    "health": 4,
    "education": 5
}

@app.route('/api/save-preferences', methods=['POST'])
def save_preferences():
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400

    # Parse JSON body (plain JSON is expected from the client)
    data = request.get_json()
    if not data or 'prefs' not in data:
        return jsonify({"error": "Invalid data format"}), 400

    prefs = data['prefs']

    try:
        # Convert 'budget' into a single numerical feature (average of the range)
        budget = (float(prefs['budget'][0]) + float(prefs['budget'][1])) / 2
    except Exception as e:
        return jsonify({"error": "Invalid budget format"}), 400

    # Convert 'interests' into numerical values using the interest_map
    interests = [interest_map.get(interest, 0) for interest in prefs.get('interests', [])]
    interests_score = sum(interests)

    # Flatten preferences for storage
    flattened_data = {
        "user_id": user_id,
        "budget": budget,
        "interests": interests_score
    }

    try:
        # Encrypt the flattened data before storing it in memory
        encrypted_data = encrypt_data(flattened_data)
    except Exception as e:
        return jsonify({"error": f"Encryption failed: {str(e)}"}), 500

    # Save the encrypted token in memory (in production, use a database)
    user_data[user_id] = encrypted_data

    # (Optional) Process through federated learning—mock implementation here.
    process_federated_update(user_id)

    return jsonify({"status": "success"})


@app.route('/api/segments')
def get_segments():
    if not user_data:
        return jsonify({"error": "No user data available"}), 400

    try:
        # Decrypt each stored user record
        decrypted_data = {uid: decrypt_data(data) for uid, data in user_data.items()}
    except Exception as e:
        return jsonify({"error": f"Decryption failed: {str(e)}"}), 500

    # Create DataFrame from the decrypted data
    df = pd.DataFrame(list(decrypted_data.values()))
    # Select only numerical columns (e.g., budget and interests)
    df_numeric = df.select_dtypes(include=[np.number])
    if df_numeric.empty:
        return jsonify({"error": "No numerical data for clustering"}), 400

    try:
        # Perform clustering using KMeans on numerical data only
        kmeans = KMeans(n_clusters=5, random_state=42)
        clusters = kmeans.fit_predict(df_numeric)
    except Exception as e:
        return jsonify({"error": f"Clustering failed: {str(e)}"}), 500

    return jsonify({
        "labels": clusters.tolist(),
        "features": df_numeric.mean().to_dict()
    })


def encrypt_data(data):
    """Serialize and encrypt data."""
    json_data = json.dumps(data).encode()  # Convert dict to JSON bytes
    return cipher.encrypt(json_data)


def decrypt_data(encrypted_data):
    """Decrypt and deserialize data."""
    decrypted = cipher.decrypt(encrypted_data)
    return json.loads(decrypted.decode())


def process_federated_update(user_id):
    """Mock federated learning processing (replace with your actual logic)."""
    pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, ssl_context=("cert.pem", "key.pem"))
