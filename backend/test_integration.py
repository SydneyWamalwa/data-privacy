# test_integration.py
import requests
import test_users
from time import sleep

def test_end_to_end():
    print("Starting integration test with 10 users...")

    # Phase 1: Submit all user preferences
    for user in test_users.users:
        response = requests.post(
            "https://localhost:5001/api/save-preferences",
            headers={"X-User-ID": user["user_id"]},
            json={"prefs": user["prefs"]},
            verify=False
        )
        print(f"Submitted {user['user_id']}: {response.status_code}")
        sleep(0.5)  # Simulate real user spacing

    # Phase 2: Verify federation triggered
    print("\nChecking federation status...")
    model_response = requests.get("https://localhost:5001/api/model", verify=False)
    assert model_response.status_code == 200
    print(f"Model version: {model_response.json()['version']}")

    # Phase 3: Verify segmentation
    segments_response = requests.get("https://localhost:5001/api/segments", verify=False)
    assert segments_response.status_code == 200
    data = segments_response.json()

    print("\nTest Results:")
    print(f"Total Users: {data['participants']}")
    print(f"Segments: {len(set(data['segments']))} unique groups")
    print(f"Avg Budget: ${data['stats']['average_budget']:.2f}")
    print(f"Top Interest: {['Tech', 'Finance', 'Sports', 'Health', 'Education'][data['stats']['common_interests']-1]}")

    # Verify all 10 users processed
    assert data['participants'] == 10
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_end_to_end()