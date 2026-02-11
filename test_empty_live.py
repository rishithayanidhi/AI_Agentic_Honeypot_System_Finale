import requests
import json

url = "https://ai-agentic-honeypot-system.onrender.com/api/message"
headers = {
    "x-api-key": "honeypot-secret-2026",
    "Content-Type": "application/json"
}

# Test empty body (what GUVI tester sends)
print("Testing empty body: {}")
response = requests.post(url, json={}, headers=headers, timeout=10)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
