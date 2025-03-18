import requests

BASE_URL = "http://127.0.0.1:5000"  # Change this if needed

params = {"title": "kitabu"}  # Simulating a search for "kitabu"
headers = {"Authorization": f"Bearer YOUR_ACCESS_TOKEN_HERE"}  # Replace with real token

response = requests.get(f"{BASE_URL}/books", params=params, headers=headers)
print("API Response:", response.json())
