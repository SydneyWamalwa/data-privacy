import requests
import random

BASE_URL = "https://localhost:5001"
INTERESTS = ["tech", "finance", "sports", "health", "education"]

def simulate_client(user_id):
    prefs = {
        "budget": [random.randint(300, 1000), random.randint(300, 1000)],
        "interests": random.sample(INTERESTS, 2)
    }

    response = requests.post(
        f"{BASE_URL}/api/save-preferences",
        headers={"X-User-ID": user_id},
        json={"prefs": prefs},
        verify=False
    )
    return response.ok

# Simulate 15 clients
for i in range(15):
    simulate_client(f"simuser{i}")
    print(f"Client {i} submitted data")

# Check federation status
model_response = requests.get(f"{BASE_URL}/api/model", verify=False)
print("Global model:", model_response.json())