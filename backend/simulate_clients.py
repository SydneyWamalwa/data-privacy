import requests
import json
import random
import webbrowser
import time

NUM_SIMULATED_USERS = 20  # adjust as needed
API_URL = "http://localhost:5001/api/save-preferences"

def generate_random_prefs():
    return {
        "prefs": {
            "budget": [random.randint(100, 500), random.randint(501, 1000)],
            "interests": random.sample(["tech", "finance", "sports", "health", "education"], 2)
        }
    }

def simulate_clients():
    for i in range(1, NUM_SIMULATED_USERS + 1):
        user_id = f"sim_user_{i}"
        headers = {"X-User-ID": user_id}
        data = generate_random_prefs()
        try:
            response = requests.post(API_URL, json=data, headers=headers)
            response.raise_for_status()
            print(f"✅ User {i} success: {response.json()}")
        except requests.exceptions.RequestException as e:
            print(f"❌ User {i} failed: {e}")

if __name__ == "__main__":
    simulate_clients()
    print("Simulation complete. Redirecting to dashboard in 3 seconds...")
    time.sleep(3)  # wait a moment for your app to update the dashboard data
    webbrowser.open("http://localhost:5001/dashboard")
