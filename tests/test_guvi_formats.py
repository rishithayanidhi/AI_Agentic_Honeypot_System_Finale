import requests
import json

url = "https://ai-agentic-honeypot-system.onrender.com/api/message"
headers = {
    "x-api-key": "honeypot-secret-2026",
    "Content-Type": "application/json"
}

# Test with minimal GUVI format (what they might be sending)
test_cases = [
    {"sessionId": "test", "message": "test message"},  # Simple flat structure
    {"session_id": "test", "message": {"text": "test"}},  # snake_case variant
    {"sessionId": "test", "message": {"text": "test"}},  # Nested but minimal
]

for i, body in enumerate(test_cases, 1):
    print(f"\n{'='*60}")
    print(f"TEST {i}: {json.dumps(body)}")
    print('='*60)
    try:
        response = requests.post(url, json=body, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
