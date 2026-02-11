"""
Test deployment response times
Compare different platforms or measure your deployment speed
"""

import requests
import time
from statistics import mean, median

def test_endpoint_speed(url, api_key, num_tests=5):
    """Test endpoint response time"""
    
    print(f"\n🧪 Testing: {url}")
    print("=" * 80)
    
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    # Test 1: Health check (cold start)
    print("\n1️⃣ Cold Start Test (Health Check)")
    start = time.time()
    try:
        response = requests.get(f"{url}/health", timeout=30)
        cold_start_time = time.time() - start
        print(f"   ✅ Cold start: {cold_start_time:.2f}s")
        print(f"   Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return
    
    # Test 2: Multiple health checks (warm)
    print(f"\n2️⃣ Warm Response Test ({num_tests} calls)")
    times = []
    for i in range(num_tests):
        start = time.time()
        try:
            response = requests.get(f"{url}/health", timeout=10)
            duration = time.time() - start
            times.append(duration)
            print(f"   Call {i+1}: {duration:.3f}s")
        except Exception as e:
            print(f"   ❌ Call {i+1} failed: {e}")
    
    if times:
        print(f"\n   📊 Average: {mean(times):.3f}s")
        print(f"   📊 Median: {median(times):.3f}s")
        print(f"   📊 Min: {min(times):.3f}s")
        print(f"   📊 Max: {max(times):.3f}s")
    
    # Test 3: Full API call (with LLM)
    print(f"\n3️⃣ Full API Test (with LLM processing)")
    payload = {
        "sessionId": "speed-test-001",
        "message": {
            "sender": "scammer",
            "text": "Your account is blocked. Share OTP immediately.",
            "timestamp": "2026-02-11T10:00:00Z"
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English"
        }
    }
    
    api_times = []
    for i in range(3):
        start = time.time()
        try:
            response = requests.post(
                f"{url}/api/message",
                headers=headers,
                json=payload,
                timeout=30
            )
            duration = time.time() - start
            api_times.append(duration)
            print(f"   Call {i+1}: {duration:.2f}s (Status: {response.status_code})")
            
            if response.status_code == 200:
                data = response.json()
                print(f"           Scam detected: {data.get('scamDetected', False)}")
        except Exception as e:
            print(f"   ❌ Call {i+1} failed: {e}")
        
        time.sleep(2)  # Wait between calls
    
    if api_times:
        print(f"\n   📊 Average API time: {mean(api_times):.2f}s")
        print(f"   📊 Median API time: {median(api_times):.2f}s")
    
    # Performance grade
    print("\n" + "=" * 80)
    if times and mean(times) < 0.5:
        print("🏆 Grade: EXCELLENT - Perfect for GUVI checker")
    elif times and mean(times) < 1.0:
        print("✅ Grade: GOOD - Suitable for GUVI checker")
    elif times and mean(times) < 3.0:
        print("⚠️  Grade: ACCEPTABLE - May work for GUVI checker")
    else:
        print("❌ Grade: SLOW - May timeout with GUVI checker")
    print("=" * 80)


if __name__ == "__main__":
    print("🚀 Deployment Speed Tester")
    print("=" * 80)
    
    # Test your deployment
    url = input("\nEnter your deployment URL (e.g., https://your-app.railway.app): ").strip()
    api_key = input("Enter your API key (default: guvi-secret-key-12345): ").strip() or "guvi-secret-key-12345"
    
    # Remove trailing slash
    url = url.rstrip('/')
    
    test_endpoint_speed(url, api_key, num_tests=5)
    
    print("\n✅ Testing complete!")
    print("\n💡 Tip: Railway should show <500ms warm response times")
    print("💡 Tip: Render may show 30-60s cold start times")
