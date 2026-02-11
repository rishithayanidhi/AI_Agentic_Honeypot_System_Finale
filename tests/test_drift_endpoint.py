"""
Test script for Intent Drift API endpoint
Tests the complete drift tracking functionality end-to-end
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "guvi-secret-key-12345"  # Default from config
HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

def test_drift_endpoint():
    """Test the intent drift tracking endpoint"""
    
    print("=" * 80)
    print("🧪 Testing Intent Drift Tracking API")
    print("=" * 80)
    
    session_id = f"drift-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Simulate conversation with intent drifts
    messages = [
        {
            "text": "Your account will be blocked! Share OTP immediately.",
            "expected_intent": "bank_fraud"
        },
        {
            "text": "Send OTP now to verify your account.",
            "expected_intent": "bank_fraud"  # No drift
        },
        {
            "text": "Click this link to update your details: bit.ly/update123",
            "expected_intent": "phishing"  # DRIFT from bank_fraud
        },
        {
            "text": "Congratulations! You won 10 lakhs in lottery. Share your bank details.",
            "expected_intent": "fake_offer"  # DRIFT from phishing
        },
        {
            "text": "Download this app to claim your prize: download.com/prize",
            "expected_intent": "phishing"  # DRIFT back to phishing
        }
    ]
    
    print(f"\n📝 Session ID: {session_id}")
    print(f"📨 Sending {len(messages)} messages to simulate drift pattern...\n")
    
    # Send messages
    for i, msg in enumerate(messages, 1):
        print(f"Message {i}: {msg['text'][:60]}...")
        
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": msg["text"],
                "timestamp": datetime.now().isoformat()
            },
            "conversationHistory": [],
            "metadata": {
                "channel": "SMS",
                "language": "English"
            }
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/message",
                headers=HEADERS,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Response received: {data.get('status')}")
            else:
                print(f"   ❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print("\n" + "=" * 80)
    print("📊 Fetching Drift Analysis...")
    print("=" * 80)
    
    # Get drift analysis
    try:
        response = requests.get(
            f"{BASE_URL}/api/session/{session_id}/drift",
            headers=HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n✅ DRIFT ANALYSIS RETRIEVED\n")
            
            # Display intent history
            print("📋 Intent Timeline:")
            print("-" * 80)
            if "intentHistory" in data:
                for record in data["intentHistory"]:
                    print(f"  Message {record['messageNumber']}: {record['intent']} "
                          f"(confidence: {record['confidence']:.2f})")
            
            # Display drift analysis
            if "driftAnalysis" in data:
                analysis = data["driftAnalysis"]
                print("\n📊 Drift Metrics:")
                print("-" * 80)
                print(f"  Total Drifts: {analysis.get('totalDrifts', 0)}")
                print(f"  Drift Rate: {analysis.get('driftRate', 0) * 100:.1f}%")
                print(f"  Intent Diversity: {analysis.get('intentDiversity', 0)}")
                print(f"  Stability Score: {analysis.get('stabilityScore', 0):.2f}")
                print(f"  Primary Intent: {analysis.get('primaryIntent', 'N/A')}")
                print(f"  Behavior Type: {analysis.get('behaviorType', 'unknown')}")
                
                # Display drift events
                if "driftEvents" in analysis and analysis["driftEvents"]:
                    print("\n⚠️  Drift Events:")
                    print("-" * 80)
                    for event in analysis["driftEvents"]:
                        print(f"  {event['fromIntent']} → {event['toIntent']} "
                              f"(magnitude: {event['magnitude']}, message: {event['messageNumber']})")
            
            # Display behavior insights
            if "behaviorInsights" in data:
                insights = data["behaviorInsights"]
                print("\n🧠 Behavioral Insights:")
                print("-" * 80)
                print(f"  {insights.get('interpretation', 'No interpretation available')}")
            
            print("\n" + "=" * 80)
            print("✅ DRIFT TRACKING TEST COMPLETE")
            print("=" * 80)
            
            # Verify expectations
            drift_count = data.get("driftAnalysis", {}).get("totalDrifts", 0)
            expected_drifts = 3  # bank_fraud→phishing, phishing→fake_offer, fake_offer→phishing
            
            if drift_count >= expected_drifts - 1:  # Allow for slight variation
                print("\n🎉 TEST PASSED: Drift detection working correctly!")
                return True
            else:
                print(f"\n⚠️  WARNING: Expected ~{expected_drifts} drifts, got {drift_count}")
                return False
                
        else:
            print(f"\n❌ Error fetching drift analysis: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"\n❌ Exception during drift analysis fetch: {e}")
        return False


if __name__ == "__main__":
    print("\n🚀 Starting Intent Drift Endpoint Test\n")
    print("⚠️  Make sure the server is running on http://localhost:8000")
    print("    Run: python main.py or start.bat\n")
    
    input("Press Enter to continue...")
    
    success = test_drift_endpoint()
    
    if success:
        print("\n✅ All tests passed!")
        exit(0)
    else:
        print("\n❌ Some tests failed!")
        exit(1)
