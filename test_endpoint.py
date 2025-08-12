import requests
import json

def test_verify_online():
    url = "http://localhost:5000/verify-online"
    data = {"text": "Modi government"}
    
    try:
        response = requests.post(url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_verify_online()
