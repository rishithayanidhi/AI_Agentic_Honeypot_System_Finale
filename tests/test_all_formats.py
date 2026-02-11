"""
Comprehensive API test for all request formats
Run this with the server running: python main.py
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_KEY = "honeypot-secret-2026"
HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

def test_format(name, body):
    """Test a specific request format"""
    print(f"\n{'='*80}")
    print(f"TEST: {name}")
    print(f"{'='*80}")
    print(f"Request body: {json.dumps(body, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/message",
            json=body,
            headers=HEADERS,
            timeout=15
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS")
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ FAILED")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

# Check if server is running
print("Checking if server is running...")
try:
    health = requests.get(f"{BASE_URL}/health", timeout=5)
    if health.status_code == 200:
        print("✅ Server is running")
        print(f"Health check: {health.json()}")
    else:
        print("❌ Server not responding properly")
        exit(1)
except Exception as e:
    print(f"❌ Cannot connect to server: {e}")
    print("Please start the server with: python main.py")
    exit(1)

print("\n" + "="*80)
print("TESTING VARIOUS REQUEST FORMATS")
print("="*80)

results = []

# Test 1: Empty body
results.append(test_format(
    "Empty body ({})",
    {}
))

# Test 2: Only sessionId
results.append(test_format(
    "Only sessionId",
    {"sessionId": "test-session-1"}
))

# Test 3: SessionId + string message
results.append(test_format(
    "SessionId + string message",
    {
        "sessionId": "test-session-2",
        "message": "Hello, I need help"
    }
))

# Test 4: SessionId + minimal message dict
results.append(test_format(
    "SessionId + minimal message dict",
    {
        "sessionId": "test-session-3",
        "message": {"text": "URGENT: Verify your bank account now!"}
    }
))

# Test 5: SessionId + full message dict
results.append(test_format(
    "SessionId + full message dict",
    {
        "sessionId": "test-session-4",
        "message": {
            "sender": "scammer",
            "text": "Your UPI account will be blocked. Share OTP immediately.",
            "timestamp": datetime.now().isoformat()
        }
    }
))

# Test 6: Full proper format
results.append(test_format(
    "Full proper format with all fields",
    {
        "sessionId": "test-session-5",
        "message": {
            "sender": "scammer",
            "text": "Congratulations! You won 10 lakhs. Share bank details to claim.",
            "timestamp": datetime.now().isoformat()
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
))

# Test 7: GUVI endpoint tester format (what they might send)
results.append(test_format(
    "GUVI tester format (minimal)",
    {
        "sessionId": "guvi-test-session",
        "message": {
            "text": "test message"
        }
    }
))

# Test 8: Snake case format
results.append(test_format(
    "Snake case variant",
    {
        "session_id": "snake-case-session",
        "message": "Testing snake_case format"
    }
))

# Summary
print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)
passed = sum(results)
total = len(results)
print(f"Passed: {passed}/{total}")
print(f"Failed: {total - passed}/{total}")

if passed == total:
    print("\n✅ All tests passed! API is ready for GUVI testing.")
else:
    print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
