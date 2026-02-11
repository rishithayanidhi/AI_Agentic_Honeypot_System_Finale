"""
Test Rate Limiting and Cooldown Features
"""
import time
from datetime import datetime, timedelta
from src.services.ai_agent import AIAgent


def test_retry_delay_extraction():
    """Test that retry delays are extracted from error messages"""
    agent = AIAgent()
    
    print("Testing retry delay extraction:")
    print("-" * 50)
    
    # Test case 1: Standard format
    error1 = "Please retry in 18.360292146s."
    delay1 = agent._extract_retry_delay(error1)
    print(f"  Error: '{error1[:40]}...'")
    print(f"  Extracted: {delay1}s {'✅' if delay1 == 18.360292146 else '❌'}")
    
    # Test case 2: RetryInfo format
    error2 = "{'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '14s'}"
    delay2 = agent._extract_retry_delay(error2)
    print(f"  Error: '{error2[:40]}...'")
    print(f"  Extracted: {delay2}s {'✅' if delay2 == 14.0 else '❌'}")
    
    # Test case 3: No delay in message
    error3 = "Generic error message"
    delay3 = agent._extract_retry_delay(error3)
    print(f"  Error: '{error3}'")
    print(f"  Extracted: {delay3}s (default) {'✅' if delay3 == 60.0 else '❌'}")
    
    print()


def test_cooldown_tracking():
    """Test cooldown setting and checking"""
    agent = AIAgent()
    
    print("Testing cooldown tracking:")
    print("-" * 50)
    
    # Set cooldown for a provider
    print("  Setting 5s cooldown for test_provider...")
    agent._set_cooldown('test_provider', 5, is_model=False)
    
    # Check immediately
    is_cooldown = agent._is_provider_in_cooldown('test_provider')
    print(f"  Is in cooldown (immediate): {is_cooldown} {'✅' if is_cooldown else '❌'}")
    
    # Wait 3 seconds
    print("  Waiting 3 seconds...")
    time.sleep(3)
    is_cooldown = agent._is_provider_in_cooldown('test_provider')
    print(f"  Is in cooldown (after 3s): {is_cooldown} {'✅' if is_cooldown else '❌'}")
    
    # Wait 3 more seconds
    print("  Waiting 3 more seconds...")
    time.sleep(3)
    is_cooldown = agent._is_provider_in_cooldown('test_provider')
    print(f"  Is in cooldown (after 6s): {is_cooldown} {'❌' if is_cooldown else '✅'}")
    
    print()


def test_model_cooldown():
    """Test per-model cooldown"""
    agent = AIAgent()
    
    print("Testing model-specific cooldown:")
    print("-" * 50)
    
    # Set cooldown for specific model
    model = "models/gemini-test"
    print(f"  Setting 3s cooldown for {model}...")
    agent._set_cooldown(model, 3, is_model=True)
    
    is_cooldown = agent._is_model_in_cooldown(model)
    print(f"  Model in cooldown: {is_cooldown} {'✅' if is_cooldown else '❌'}")
    
    # Wait for expiry
    print("  Waiting for cooldown to expire...")
    time.sleep(4)
    
    is_cooldown = agent._is_model_in_cooldown(model)
    print(f"  Model still in cooldown: {is_cooldown} {'❌' if is_cooldown else '✅'}")
    
    print()


def test_throttling():
    """Test request throttling"""
    agent = AIAgent()
    
    print("Testing request throttling:")
    print("-" * 50)
    
    # First request
    print("  Making first request...")
    start = time.time()
    agent._throttle_request('test_provider')
    elapsed1 = time.time() - start
    print(f"  First request delay: {elapsed1:.2f}s (should be ~0s) {'✅' if elapsed1 < 0.1 else '❌'}")
    
    # Second request immediately after
    print("  Making second request (should throttle)...")
    start = time.time()
    agent._throttle_request('test_provider')
    elapsed2 = time.time() - start
    print(f"  Second request delay: {elapsed2:.2f}s (should be ~12s) {'✅' if 11 < elapsed2 < 13 else '❌'}")
    
    print()


def test_api_keys():
    """Test API key configuration"""
    agent = AIAgent()
    
    print("Testing API key configuration:")
    print("-" * 50)
    
    print(f"  Available providers: {agent.available_providers}")
    print(f"  Gemini clients: {len(agent.gemini_clients)}")
    
    if agent.gemini_clients:
        print(f"  Current key index: {agent.gemini_key_index}")
        print("  ✅ Gemini configured")
    else:
        print("  ⚠️  No Gemini keys configured")
    
    if 'anthropic' in agent.available_providers:
        print("  ✅ Anthropic configured")
    else:
        print("  ⚠️  Anthropic not configured")
    
    print()


def main():
    print("=" * 60)
    print("RATE LIMITING TESTS")
    print("=" * 60)
    print()
    
    try:
        test_retry_delay_extraction()
        test_cooldown_tracking()
        test_model_cooldown()
        test_throttling()
        test_api_keys()
        
        print("=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Run: python monitor_api_status.py")
        print("  2. Check your deployed service logs")
        print("  3. Look for throttling and cooldown messages")
        print()
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
