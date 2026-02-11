"""Test what the GUVI tester might be sending"""
import requests
import json

url = "http://localhost:8000/api/message"
headers = {
    "x-api-key": "honeypot-secret-2026",
    "Content-Type": "application/json"
}

print("Testing what GUVI endpoint tester might send...")
print("=" * 80)

# Test 1: Completely empty body
print("\n1. Empty JSON body: {}")
try:
    r = requests.post(url, json={}, headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print(f"✅ SUCCESS")
    else:
        print(f"❌ FAILED: {r.text[:200]}")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Test 2: No body at all (null)
print("\n2. Null body")
try:
    r = requests.post(url, json=None, headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print(f"✅ SUCCESS")
    else:
        print(f"❌ FAILED: {r.text[:200]}")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Test 3: No json parameter (raw empty body)
print("\n3. Raw request with no data")
try:
    r = requests.post(url, headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print(f"✅ SUCCESS")
    else:
        print(f"❌ FAILED: {r.text[:200]}")
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n" + "=" * 80)
print("Testing complete!")
