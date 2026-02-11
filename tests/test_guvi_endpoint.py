"""
GUVI Endpoint Verification Script
Tests if your honeypot API meets GUVI requirements
"""

import sys
import os
import warnings

# Suppress Pydantic warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic._internal._fields")

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Change to project root for .env
if os.path.basename(os.getcwd()) == 'tests':
    os.chdir('..')

import requests
import json
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

# Configuration
BASE_URL = "http://localhost:8000"  # Change to your deployed URL
API_KEY = "honeypot-secret-2026"

def print_header(text):
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{text}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

def print_success(text):
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")

def print_error(text):
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")

def print_info(text):
    print(f"{Fore.YELLOW}ℹ️  {text}{Style.RESET_ALL}")

def test_health_check():
    """Test 1: Health check endpoint (no auth)"""
    print_header("Test 1: Health Check Endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health check passed")
            print_info(f"Status: {data.get('status')}")
            print_info(f"Active sessions: {data.get('active_sessions')}")
            print_info(f"LLM provider: {data.get('llm_provider')}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check error: {str(e)}")
        return False

def test_authentication():
    """Test 2: API key authentication"""
    print_header("Test 2: API Key Authentication")
    
    # Test without API key
    try:
        response = requests.post(
            f"{BASE_URL}/api/message",
            json={"session_id": "test", "message": "test"},
            timeout=15
        )
        
        if response.status_code == 403:
            print_success("Authentication check passed (no key rejected)")
        else:
            print_error(f"Expected 403, got {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Auth test error: {str(e)}")
        return False
    
    # Test with wrong API key
    try:
        response = requests.post(
            f"{BASE_URL}/api/message",
            headers={"x-api-key": "wrong-key"},
            json={"session_id": "test", "message": "test"},
            timeout=15
        )
        
        if response.status_code == 403:
            print_success("Wrong key rejected correctly")
            return True
        else:
            print_error(f"Expected 403 for wrong key, got {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Wrong key test error: {str(e)}")
        return False

def test_scam_detection():
    """Test 3: Scam detection and response"""
    print_header("Test 3: Scam Detection & Response Format")
    
    test_message = {
        "sessionId": "guvi-test-001",
        "message": {
            "sender": "scammer",
            "text": "Your bank account is blocked. Share OTP to verify immediately.",
            "timestamp": datetime.now().isoformat()
        },
        "conversationHistory": []
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/message",
            headers={
                "x-api-key": API_KEY,
                "Content-Type": "application/json"
            },
            json=test_message,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields
            required_fields = [
                'sessionId', 'response', 'isScam', 'scamType', 
                'confidence', 'reasoning', 'shouldContinue',
                'engagementMetrics', 'extractedIntelligence'
            ]
            
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                print_error(f"Missing required fields: {missing_fields}")
                return False
            
            print_success("All required fields present")
            print_info(f"Session ID: {data['sessionId']}")
            print_info(f"Is Scam: {data['isScam']}")
            print_info(f"Scam Type: {data['scamType']}")
            print_info(f"Confidence: {data['confidence']*100:.1f}%")
            print_info(f"AI Response: {data['response'][:100]}...")
            print_info(f"Reasoning: {data['reasoning'][:100]}...")
            
            # Validate scam detection (confidence is 0-1 range)
            if data['isScam'] and data['confidence'] >= 0.85:
                print_success(f"Scam detected correctly with {data['confidence']*100:.1f}% confidence")
                return True
            else:
                print_error(f"Scam detection failed: isScam={data['isScam']}, confidence={data['confidence']*100:.1f}%")
                return False
        else:
            print_error(f"Request failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Scam detection test error: {str(e)}")
        return False

def test_simple_format():
    """Test 4: Simple format support"""
    print_header("Test 4: Simple Message Format Support")
    
    simple_message = {
        "session_id": "guvi-test-002",
        "message": "Click this link to claim your prize: bit.ly/prize123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/message",
            headers={
                "x-api-key": API_KEY,
                "Content-Type": "application/json"
            },
            json=simple_message,
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('isScam') and data.get('confidence', 0) >= 0.5:
                print_success("Simple format works correctly")
                print_info(f"Detected: {data['scamType']} ({data.get('confidence', 0)*100:.1f}%)")
                return True
            else:
                print_error(f"Simple format detection failed: isScam={data.get('isScam')}, scamType={data.get('scamType')}, confidence={data.get('confidence', 0)*100:.1f}%")
                return False
        else:
            print_error(f"Simple format request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Simple format test error: {str(e)}")
        return False

def test_performance():
    """Test 5: Response time check"""
    print_header("Test 5: Performance & Response Time")
    
    test_message = {
        "session_id": "guvi-test-003",
        "message": "Send ₹1 to verify your account"
    }
    
    try:
        import time
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/api/message",
            headers={
                "x-api-key": API_KEY,
                "Content-Type": "application/json"
            },
            json=test_message,
            timeout=10
        )
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            if response_time < 3.0:
                print_success(f"Response time: {response_time:.2f}s (Excellent)")
                return True
            elif response_time < 5.0:
                print_success(f"Response time: {response_time:.2f}s (Good)")
                return True
            else:
                print_error(f"Response time: {response_time:.2f}s (Too slow)")
                return False
        else:
            print_error(f"Performance test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Performance test error: {str(e)}")
        return False

def main():
    """Run all GUVI endpoint verification tests"""
    print(f"\n{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}🎯 GUVI Honeypot Endpoint Verification{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
    
    print_info(f"Testing endpoint: {BASE_URL}")
    print_info(f"API Key: {API_KEY}")
    
    # Run all tests
    results = []
    
    results.append(("Health Check", test_health_check()))
    results.append(("Authentication", test_authentication()))
    results.append(("Scam Detection", test_scam_detection()))
    results.append(("Simple Format", test_simple_format()))
    results.append(("Performance", test_performance()))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    if passed == total:
        print(f"{Fore.GREEN}🎉 All tests passed! ({passed}/{total}){Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Your endpoint is READY for GUVI submission!{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⚠️  {passed}/{total} tests passed{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Some tests failed. Please review and fix.{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    # Deployment info
    if passed == total:
        print_header("Next Steps - Deploy Your Endpoint")
        print("1. Deploy to Railway/Render/Ngrok")
        print("2. Update BASE_URL in this script to your deployed URL")
        print("3. Run this script again to verify deployed endpoint")
        print("4. Submit to GUVI with:")
        print(f"   - URL: {BASE_URL}/api/message")
        print(f"   - Header: x-api-key")
        print(f"   - Value: {API_KEY}")
        print()

if __name__ == "__main__":
    main()
