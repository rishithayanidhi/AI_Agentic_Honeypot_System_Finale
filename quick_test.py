"""Quick test for empty body and minimal format"""
import requests
import json

url = "http://localhost:8000/api/message"
headers = {
    "x-api-key": "honeypot-secret-2026",
    "Content-Type": "application/json"
}

print("Testing GUVI formats...")
print("=" * 80)

# Test 1: Empty body
print("\n1. Empty body: {}")
try:
    r = requests.post(url, json={}, headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print(f"✅ SUCCESS: {json.dumps(r.json(), indent=2)}")
    else:
        print(f"❌ FAILED: {r.text}")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Test 2: Minimal format
print("\n2. Minimal format: {\"sessionId\": \"test\", \"message\": {\"text\": \"test\"}}")
try:
    r = requests.post(
        url, 
        json={"sessionId": "test", "message": {"text": "test"}}, 
        headers=headers, 
        timeout=10
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print(f"✅ SUCCESS: {json.dumps(r.json(), indent=2)}")
    else:
        print(f"❌ FAILED: {r.text}")
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n" + "=" * 80)
print("Tests complete!")
