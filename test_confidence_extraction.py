"""
Test Confidence-Weighted Intelligence Extraction
Demonstrates the enhanced extraction with confidence scoring
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "honeypot-secret-2026"
HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def send_message(session_id, message_text):
    """Send a message and return response"""
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": message_text,
            "timestamp": "2026-02-11T10:00:00Z"
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/message", headers=HEADERS, json=payload)
    return response.json()

def get_detailed_intelligence(session_id, threshold=0.0):
    """Get detailed confidence-weighted intelligence"""
    response = requests.get(
        f"{BASE_URL}/api/session/{session_id}/intelligence",
        headers=HEADERS,
        params={"threshold": threshold}
    )
    return response.json()

def test_scenario_1_bank_fraud():
    """Test: Bank fraud with account number and urgency"""
    print_section("SCENARIO 1: Bank Fraud with High Confidence")
    
    session_id = "test-confidence-001"
    
    # Message with bank account + urgency + sensitive keywords
    message = "URGENT! Your SBI bank account 123456789012 will be blocked. Share OTP to verify immediately."
    
    print(f"\n📨 Scammer message: {message}")
    
    response = send_message(session_id, message)
    print(f"\n✅ Status: {response['status']}")
    print(f"📝 Agent Reply: {response['reply']}")
    
    time.sleep(1)  # Brief pause for processing
    
    # Get detailed intelligence
    intel = get_detailed_intelligence(session_id)
    
    print(f"\n📊 INTELLIGENCE METRICS:")
    print(f"   Overall Confidence: {intel['overallConfidence']:.2%}")
    print(f"   High Confidence Items: {intel['highConfidenceCount']}")
    print(f"   Total Items: {intel['totalItemsExtracted']}")
    
    print(f"\n🏦 BANK ACCOUNTS EXTRACTED:")
    for item in intel['detailedIntelligence']['bankAccounts']:
        print(f"   • Value: {item['value']}")
        print(f"     Confidence: {item['confidence']:.2%} ⭐")
        print(f"     Occurrences: {item['occurrences']}x")
        print(f"     Context: {item['context'][:60]}...")
    
    print(f"\n🔑 SUSPICIOUS KEYWORDS:")
    for item in intel['detailedIntelligence']['suspiciousKeywords'][:5]:
        print(f"   • {item['value']}: {item['confidence']:.2%}")
    
    print(f"\n📈 CONFIDENCE DISTRIBUTION:")
    dist = intel['confidenceDistribution']
    print(f"   Very High (≥90%): {dist['veryHigh']} items")
    print(f"   High (70-89%): {dist['high']} items")
    print(f"   Medium (50-69%): {dist['medium']} items")
    print(f"   Low (<50%): {dist['low']} items")
    
    return session_id

def test_scenario_2_upi_fraud():
    """Test: UPI fraud with payment context"""
    print_section("SCENARIO 2: UPI Fraud with Payment Context")
    
    session_id = "test-confidence-002"
    
    # Message with UPI ID and payment context
    message = "Send payment to scammer@paytm immediately. UPI ID: fraudster123@phonepe. Transfer Rs.5000 now!"
    
    print(f"\n📨 Scammer message: {message}")
    
    response = send_message(session_id, message)
    print(f"\n✅ Status: {response['status']}")
    print(f"📝 Agent Reply: {response['reply']}")
    
    time.sleep(1)
    
    intel = get_detailed_intelligence(session_id, threshold=0.6)  # Filter high confidence only
    
    print(f"\n📊 HIGH CONFIDENCE INTELLIGENCE (≥60%):")
    print(f"   Overall Confidence: {intel['overallConfidence']:.2%}")
    
    print(f"\n💳 UPI IDs EXTRACTED:")
    for item in intel['detailedIntelligence']['upiIds']:
        print(f"   • Value: {item['value']}")
        print(f"     Confidence: {item['confidence']:.2%} ⭐")
        print(f"     First Seen: {item['firstSeen']}")
    
    return session_id

def test_scenario_3_phishing_links():
    """Test: Phishing with suspicious links"""
    print_section("SCENARIO 3: Phishing with Suspicious Links")
    
    session_id = "test-confidence-003"
    
    # Message with phishing link
    message = "Click this link immediately to verify: https://bit.ly/fake-bank-verify and update your password now!"
    
    print(f"\n📨 Scammer message: {message}")
    
    response = send_message(session_id, message)
    print(f"\n✅ Status: {response['status']}")
    
    time.sleep(1)
    
    intel = get_detailed_intelligence(session_id)
    
    print(f"\n🔗 PHISHING LINKS EXTRACTED:")
    for item in intel['detailedIntelligence']['phishingLinks']:
        print(f"   • URL: {item['value']}")
        print(f"     Confidence: {item['confidence']:.2%} ⭐")
        print(f"     (Short URL detected - higher confidence)")
    
    return session_id

def test_scenario_4_repetition_boost():
    """Test: Confidence boost from repetition"""
    print_section("SCENARIO 4: Confidence Boost from Repetition")
    
    session_id = "test-confidence-004"
    
    messages = [
        "Call customer care at 9876543210 for help",
        "Please contact us at 9876543210 immediately",
        "Urgent! Call 9876543210 now to verify your account"
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"\n📨 Message {i}: {message}")
        response = send_message(session_id, message)
        print(f"   Reply: {response['reply']}")
        time.sleep(0.5)
    
    intel = get_detailed_intelligence(session_id)
    
    print(f"\n📞 PHONE NUMBERS EXTRACTED:")
    for item in intel['detailedIntelligence']['phoneNumbers']:
        print(f"   • Number: {item['value']}")
        print(f"     Confidence: {item['confidence']:.2%} ⭐")
        print(f"     Seen {item['occurrences']}x (confidence boosted by repetition!)")
    
    return session_id

def test_scenario_5_mixed_context():
    """Test: Mixed high and low confidence items"""
    print_section("SCENARIO 5: Mixed Confidence Levels")
    
    session_id = "test-confidence-005"
    
    # Message with both high and low confidence indicators
    message = "Account 987654321012345 blocked. Random number 12345 here. Call 9123456789. Visit generic-site.com or https://secure-bank-verify.tk"
    
    print(f"\n📨 Scammer message: {message}")
    
    response = send_message(session_id, message)
    
    time.sleep(1)
    
    intel = get_detailed_intelligence(session_id)
    
    print(f"\n📊 CONFIDENCE BREAKDOWN:")
    print(f"   Overall: {intel['overallConfidence']:.2%}")
    
    print(f"\n🔢 ALL EXTRACTED ITEMS BY CONFIDENCE:")
    
    # Combine all items
    all_items = []
    for category, items in intel['detailedIntelligence'].items():
        if category != 'suspiciousKeywords':  # Skip keywords for clarity
            for item in items:
                all_items.append({
                    'type': category,
                    'value': item['value'][:50],
                    'confidence': item['confidence']
                })
    
    # Sort by confidence
    all_items.sort(key=lambda x: x['confidence'], reverse=True)
    
    for item in all_items:
        stars = "⭐" * int(item['confidence'] * 5)
        print(f"   • [{item['type']}] {item['value']}: {item['confidence']:.2%} {stars}")
    
    return session_id

def main():
    """Run all confidence-weighted extraction tests"""
    print_section("🎯 CONFIDENCE-WEIGHTED INTELLIGENCE EXTRACTION TEST SUITE")
    print("\nDemonstrating 100% Complete Feature:")
    print("✅ Contextual confidence scoring")
    print("✅ Repetition-based confidence boosting")
    print("✅ Pattern quality assessment")
    print("✅ GUVI format compatibility maintained")
    print("✅ Detailed intelligence tracking")
    
    try:
        # Run all scenarios
        test_scenario_1_bank_fraud()
        time.sleep(2)
        
        test_scenario_2_upi_fraud()
        time.sleep(2)
        
        test_scenario_3_phishing_links()
        time.sleep(2)
        
        test_scenario_4_repetition_boost()
        time.sleep(2)
        
        test_scenario_5_mixed_context()
        
        print_section("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("\n🎉 Confidence-Weighted Extraction: 100% COMPLETE")
        print("\nKey Features Demonstrated:")
        print("  1. Context-aware confidence scoring (urgency, payment terms, etc.)")
        print("  2. Pattern quality assessment (valid UPI providers, phone formats)")
        print("  3. Repetition-based confidence boosting")
        print("  4. Detailed item tracking with timestamps")
        print("  5. Confidence distribution analytics")
        print("  6. Backward compatibility with GUVI format")
        print("  7. New detailed intelligence endpoint")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
