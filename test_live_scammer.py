"""
Live Scammer Conversation Simulator
Simulates realistic multi-turn scammer conversations to test your deployed system
"""

import requests
import json
from datetime import datetime
import time
import sys

# ===================================
# CONFIGURATION - UPDATE THESE!
# ===================================

# Your deployed URL (Render or Railway)
BASE_URL = "https://ai-agentic-honeypot-system-finale.onrender.com"  # ⚠️ CHANGE THIS!

# Your API key
API_KEY = "honeypot-secret-2026"  # Your actual API key

# ===================================
# Realistic Scammer Conversations
# ===================================

SCAMMER_SCENARIOS = {
    "bank_fraud": [
        "URGENT: Your account will be blocked in 2 hours due to suspicious activity.",
        "You need to verify your account immediately by sharing OTP.",
        "I am calling from State Bank of India security department.",
        "Please share the OTP we just sent to your mobile: 123456",
        "If you don't share OTP, your account will be permanently blocked.",
        "I need your card CVV to reverse the fraudulent transaction.",
        "Transfer ₹1 to this UPI: security@sbi to verify your account.",
    ],
    
    "upi_fraud": [
        "Congratulations! You have won ₹50,000 in Google Pay lucky draw.",
        "To claim your prize, share your Google Pay UPI ID.",
        "My UPI ID is rewards@paytm - send ₹1 to verify your account.",
        "Now send the OTP you received to complete verification.",
        "You need to pay ₹500 processing fee to receive ₹50,000.",
    ],
    
    "phishing": [
        "Your KYC is pending. Update immediately or account will be suspended.",
        "Click this link to update: bit.ly/kyc-update-urgent",
        "If link doesn't work, go to sbi-kyc-update.com and enter your details.",
        "You need to enter card number, CVV, and OTP on that website.",
        "Don't worry, it's completely secure official website.",
    ],
    
    "lottery_scam": [
        "Congratulations! You won ₹25 lakhs in KBC lucky draw!",
        "To claim prize, you need to pay ₹5,000 processing fee first.",
        "Send money to this account: 1234567890, IFSC: SBIN0001234",
        "After payment, prize money will be transferred within 24 hours.",
        "This is genuine offer from Sony TV and Amitabh Bachchan.",
    ],
    
    "tech_support": [
        "This is Microsoft technical support. Your Windows license expired.",
        "We detected virus on your computer. Need immediate action.",
        "Download this teamviewer: download-teamviewer.info/secure",
        "Give me the teamviewer ID so I can fix your computer.",
        "There will be ₹2,999 charge for virus removal service.",
    ]
}

# ===================================
# Test Functions
# ===================================

def send_message(session_id, message_text, message_number=1):
    """Send a message to the API and get response"""
    
    url = f"{BASE_URL}/api/message"
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": message_text,
            "timestamp": datetime.now().isoformat() + "Z"
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    try:
        print(f"\n📤 Message #{message_number} (Scammer):")
        print(f"   {message_text}")
        print(f"   Sending... ", end="", flush=True)
        
        start_time = time.time()
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        duration = time.time() - start_time
        
        print(f"✅ ({duration:.2f}s)")
        
        if response.status_code == 200:
            data = response.json()
            
            # Show agent response
            if data.get("agentResponse"):
                print(f"\n💬 Agent Response:")
                print(f"   {data['agentResponse']}")
            
            # Show scam detection
            print(f"\n🔍 Detection:")
            print(f"   Scam Detected: {data.get('scamDetected', False)}")
            if data.get('agentNotes'):
                print(f"   Type: {data['agentNotes']}")
            
            # Show extracted intelligence
            intel = data.get('extractedIntelligence', {})
            if any([intel.get('bankAccounts'), intel.get('upiIds'), 
                   intel.get('phishingLinks'), intel.get('phoneNumbers')]):
                print(f"\n🎯 Intelligence Extracted:")
                if intel.get('bankAccounts'):
                    print(f"   💳 Bank Accounts: {', '.join(intel['bankAccounts'])}")
                if intel.get('upiIds'):
                    print(f"   💰 UPI IDs: {', '.join(intel['upiIds'])}")
                if intel.get('phishingLinks'):
                    print(f"   🔗 Links: {', '.join(intel['phishingLinks'])}")
                if intel.get('phoneNumbers'):
                    print(f"   📱 Phone Numbers: {', '.join(intel['phoneNumbers'])}")
            
            return data
            
        else:
            print(f"\n❌ Error: Status {response.status_code}")
            print(f"   {response.text}")
            return None
            
    except requests.Timeout:
        print(f"\n⏱️  Timeout after 30s - app may be waking up")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


def test_conversation(scenario_name, messages, delay=2):
    """Test a complete scammer conversation"""
    
    session_id = f"live-test-{scenario_name}-{int(time.time())}"
    
    print("\n" + "="*80)
    print(f"🎭 TESTING SCENARIO: {scenario_name.upper().replace('_', ' ')}")
    print("="*80)
    print(f"Session ID: {session_id}")
    print(f"Messages: {len(messages)}")
    
    results = []
    
    for i, message in enumerate(messages, 1):
        result = send_message(session_id, message, i)
        results.append(result)
        
        if result and result.get('sessionComplete'):
            print(f"\n⛔ Session ended by agent (safety)")
            break
        
        # Wait between messages to simulate real conversation
        if i < len(messages):
            print(f"\n⏳ Waiting {delay}s before next message...")
            time.sleep(delay)
    
    # Summary
    print("\n" + "="*80)
    print("📊 CONVERSATION SUMMARY")
    print("="*80)
    
    total_intel = {
        'bankAccounts': set(),
        'upiIds': set(),
        'phishingLinks': set(),
        'phoneNumbers': set()
    }
    
    for result in results:
        if result and result.get('extractedIntelligence'):
            intel = result['extractedIntelligence']
            total_intel['bankAccounts'].update(intel.get('bankAccounts', []))
            total_intel['upiIds'].update(intel.get('upiIds', []))
            total_intel['phishingLinks'].update(intel.get('phishingLinks', []))
            total_intel['phoneNumbers'].update(intel.get('phoneNumbers', []))
    
    print(f"✅ Messages Sent: {len(messages)}")
    print(f"✅ Responses Received: {sum(1 for r in results if r)}")
    print(f"\n🎯 Total Intelligence Collected:")
    print(f"   💳 Bank Accounts: {len(total_intel['bankAccounts'])}")
    print(f"   💰 UPI IDs: {len(total_intel['upiIds'])}")
    print(f"   🔗 Phishing Links: {len(total_intel['phishingLinks'])}")
    print(f"   📱 Phone Numbers: {len(total_intel['phoneNumbers'])}")
    
    if any(total_intel.values()):
        print(f"\n📋 Extracted Items:")
        if total_intel['bankAccounts']:
            print(f"   Accounts: {', '.join(total_intel['bankAccounts'])}")
        if total_intel['upiIds']:
            print(f"   UPI IDs: {', '.join(total_intel['upiIds'])}")
        if total_intel['phishingLinks']:
            print(f"   Links: {', '.join(total_intel['phishingLinks'])}")
        if total_intel['phoneNumbers']:
            print(f"   Numbers: {', '.join(total_intel['phoneNumbers'])}")
    
    return results


def test_single_message():
    """Quick single message test"""
    print("\n🧪 QUICK TEST - Single Message")
    print("="*80)
    
    test_message = "Your account is blocked! Share OTP immediately to unblock."
    session_id = f"quick-test-{int(time.time())}"
    
    result = send_message(session_id, test_message, 1)
    
    if result:
        print("\n✅ System is working!")
        return True
    else:
        print("\n❌ System test failed!")
        return False


# ===================================
# Main Menu
# ===================================

def main():
    """Main test interface"""
    
    print("="*80)
    print("🤖 LIVE SCAMMER CONVERSATION SIMULATOR")
    print("="*80)
    print(f"Target: {BASE_URL}")
    print(f"API Key: {API_KEY[:20]}...")
    
    # Check configuration
    if "your-app-name" in BASE_URL:
        print("\n❌ ERROR: Please update BASE_URL with your actual deployment URL!")
        print("   Edit this file and change BASE_URL at the top")
        sys.exit(1)
    
    print("\n📋 Available Tests:")
    print("")
    print("1. Quick Test (1 message)")
    print("2. Bank Fraud Scenario (7 messages)")
    print("3. UPI Fraud Scenario (5 messages)")
    print("4. Phishing Scenario (5 messages)")
    print("5. Lottery Scam Scenario (5 messages)")
    print("6. Tech Support Scam (5 messages)")
    print("7. Run ALL Scenarios")
    print("8. Custom Message")
    print("0. Exit")
    print("")
    
    choice = input("Select test number (0-8): ").strip()
    
    if choice == "0":
        print("\n👋 Goodbye!")
        return
    
    elif choice == "1":
        test_single_message()
    
    elif choice == "2":
        test_conversation("bank_fraud", SCAMMER_SCENARIOS["bank_fraud"])
    
    elif choice == "3":
        test_conversation("upi_fraud", SCAMMER_SCENARIOS["upi_fraud"])
    
    elif choice == "4":
        test_conversation("phishing", SCAMMER_SCENARIOS["phishing"])
    
    elif choice == "5":
        test_conversation("lottery_scam", SCAMMER_SCENARIOS["lottery_scam"])
    
    elif choice == "6":
        test_conversation("tech_support", SCAMMER_SCENARIOS["tech_support"])
    
    elif choice == "7":
        for scenario_name, messages in SCAMMER_SCENARIOS.items():
            test_conversation(scenario_name, messages)
            print("\n⏳ Waiting 5s before next scenario...")
            time.sleep(5)
    
    elif choice == "8":
        custom_msg = input("\nEnter custom scammer message: ").strip()
        if custom_msg:
            session_id = f"custom-{int(time.time())}"
            send_message(session_id, custom_msg, 1)
    
    else:
        print("\n❌ Invalid choice!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
