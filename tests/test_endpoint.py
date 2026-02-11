import requests
import json

url = "https://ai-agentic-honeypot-system.onrender.com/api/message"
headers = {
    "x-api-key": "honeypot-secret-2026",
    "Content-Type": "application/json"
}

# Test 1: Empty body (what the tester might be sending)
print("=" * 80)
print("TEST 1: Empty body")
print("=" * 80)
response = requests.post(url, headers=headers, json={})
print(f"Status Code: {response.status_code}")
print(f"Response:\n{json.dumps(response.json(), indent=2)}\n")

# Test 2: Correct format
print("=" * 80)
print("TEST 2: Correct format")
print("=" * 80)
body = {
    "sessionId": "test-123",
    "message": {
        "sender": "scammer",
        "text": "URGENT: Your account will be blocked. Share OTP now.",
        "timestamp": "2026-02-01T15:00:00Z"
    },
    "conversationHistory": [],
    "metadata": {
        "channel": "SMS",
        "language": "English",
        "locale": "IN"
    }
}
response = requests.post(url, headers=headers, json=body)
print(f"Status Code: {response.status_code}")
print(f"Response:\n{json.dumps(response.json(), indent=2)}\n")
