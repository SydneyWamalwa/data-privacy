import requests
import random
import time

BASE_URL = "http://localhost:5001"
INTERESTS = ["tech", "finance", "sports", "health", "education"]

def simulate_client(user_id):
    try:
        prefs = {
            "budget": [random.randint(300, 1000), random.randint(300, 1000)],
            "interests": random.sample(INTERESTS, random.randint(1, 3))
        }

        response = requests.post(
            f"{BASE_URL}/api/save-preferences",
            headers={"X-User-ID": user_id},
            json={"prefs": prefs},
            verify=False  # For self-signed cert
        )
        return response.ok
    except Exception as e:
        print(f"Error for {user_id}: {str(e)}")
        return False

if __name__ == "__main__":
    # Simulate 15 clients with realistic spacing
    for i in range(1, 16):
        user_id = f"sim_user_{i}"
        if simulate_client(user_id):
            print(f"✅ User {i} submitted preferences")
        else:
            print(f"❌ User {i} failed")
        time.sleep(0.5)  # Simulate real user behavior

    print("\nSimulation complete. Check dashboard at http://localhost:5001")