import requests
import json
from datetime import datetime


class HoneypotTester:
    """Test client for the Honeypot API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "your-secret-api-key-here"):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
    
    def send_message(self, session_id: str, message: str, sender: str = "scammer", conversation_history: list = None):
        """Send a message to the API"""
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": sender,
                "text": message,
                "timestamp": datetime.now().isoformat()
            },
            "conversationHistory": conversation_history or [],
            "metadata": {
                "channel": "SMS",
                "language": "English",
                "locale": "IN"
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/message",
            headers=self.headers,
            json=payload
        )
        
        return response.json()
    
    def test_bank_fraud_scenario(self):
        """Test a typical bank fraud scam scenario"""
        print("\n=== Testing Bank Fraud Scenario ===\n")
        
        session_id = "test-bank-fraud-001"
        
        # Message 1: Initial scam message
        print("Scammer: Your bank account will be blocked today. Verify immediately.")
        response = self.send_message(
            session_id=session_id,
            message="Your bank account will be blocked today. Verify immediately."
        )
        print(f"Agent Response: {response.get('agentResponse')}")
        print(f"Scam Detected: {response.get('scamDetected')}\n")
        
        # Message 2: Follow-up
        if response.get('agentResponse'):
            print(f"Scammer: Share your UPI ID to avoid account suspension.")
            response = self.send_message(
                session_id=session_id,
                message="Share your UPI ID to avoid account suspension."
            )
            print(f"Agent Response: {response.get('agentResponse')}")
            print(f"Intelligence: {response.get('extractedIntelligence')}\n")
        
        # Message 3: Provide fake details
        if response.get('agentResponse'):
            print(f"Scammer: Send money to this UPI: scammer123@paytm to verify your account.")
            response = self.send_message(
                session_id=session_id,
                message="Send money to this UPI: scammer123@paytm to verify your account."
            )
            print(f"Agent Response: {response.get('agentResponse')}")
            print(f"Intelligence: {response.get('extractedIntelligence')}\n")
        
        print(f"Session Complete: {response.get('sessionComplete')}")
        print(f"Final Notes: {response.get('agentNotes')}")
        
        return response
    
    def test_phishing_scenario(self):
        """Test a phishing link scenario"""
        print("\n=== Testing Phishing Scenario ===\n")
        
        session_id = "test-phishing-001"
        
        print("Scammer: Congratulations! You won ₹50,000. Click here to claim: http://fake-bank-site.com/claim")
        response = self.send_message(
            session_id=session_id,
            message="Congratulations! You won ₹50,000. Click here to claim: http://fake-bank-site.com/claim"
        )
        print(f"Agent Response: {response.get('agentResponse')}")
        print(f"Scam Detected: {response.get('scamDetected')}")
        print(f"Intelligence: {response.get('extractedIntelligence')}\n")
        
        return response
    
    def test_multi_turn_conversation(self):
        """Test a longer multi-turn conversation"""
        print("\n=== Testing Multi-Turn Conversation ===\n")
        
        session_id = "test-multi-turn-001"
        conversation_history = []
        
        messages = [
            "Your KYC is pending. Update immediately or account will be frozen.",
            "You need to verify with OTP. What is your registered mobile number?",
            "Send ₹1 to this account to verify: 1234567890123456",
            "Or use UPI: verify@okaxis",
            "Call this number for help: +919876543210"
        ]
        
        for i, msg in enumerate(messages, 1):
            print(f"\nMessage {i}")
            print(f"Scammer: {msg}")
            
            response = self.send_message(
                session_id=session_id,
                message=msg,
                conversation_history=conversation_history
            )
            
            agent_response = response.get('agentResponse')
            print(f"Agent: {agent_response}")
            
            # Update conversation history
            conversation_history.append({
                "sender": "scammer",
                "text": msg,
                "timestamp": datetime.now().isoformat()
            })
            
            if agent_response:
                conversation_history.append({
                    "sender": "user",
                    "text": agent_response,
                    "timestamp": datetime.now().isoformat()
                })
            
            print(f"Intelligence: {response.get('extractedIntelligence')}")
            
            if response.get('sessionComplete'):
                print("\n=== Session Completed ===")
                break
        
        print(f"\nFinal Intelligence Extracted:")
        print(json.dumps(response.get('extractedIntelligence'), indent=2))
        print(f"\nAgent Notes: {response.get('agentNotes')}")
        
        return response
    
    def health_check(self):
        """Check if API is running"""
        try:
            response = requests.get(f"{self.base_url}/health")
            print(f"Health Check: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False


if __name__ == "__main__":
    # Initialize tester
    tester = HoneypotTester()
    
    # Check health
    if not tester.health_check():
        print("API is not running! Start the server first.")
        exit(1)
    
    # Run tests
    print("\n" + "="*60)
    print("AI AGENTIC HONEYPOT - TEST SUITE")
    print("="*60)
    
    # Test 1: Bank fraud
    tester.test_bank_fraud_scenario()
    
    # Test 2: Phishing
    tester.test_phishing_scenario()
    
    # Test 3: Multi-turn conversation
    tester.test_multi_turn_conversation()
    
    print("\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)
