"""Test the flexible schema with various input formats"""
import json
from src.models.schemas import IncomingRequest, Message
from datetime import datetime

print("Testing Flexible Schema Validation")
print("=" * 80)

# Test 1: Empty body
print("\n1. Testing empty body...")
try:
    req = IncomingRequest()
    print(f"✅ Empty body accepted: {req.model_dump()}")
except Exception as e:
    print(f"❌ Failed: {e}")

# Test 2: Only sessionId
print("\n2. Testing only sessionId...")
try:
    req = IncomingRequest(sessionId="test-123")
    print(f"✅ SessionId only accepted: {req.model_dump()}")
except Exception as e:
    print(f"❌ Failed: {e}")

# Test 3: SessionId + string message
print("\n3. Testing sessionId + string message...")
try:
    req = IncomingRequest(sessionId="test-123", message="Hello")
    print(f"✅ String message accepted: {req.model_dump()}")
except Exception as e:
    print(f"❌ Failed: {e}")

# Test 4: SessionId + dict message
print("\n4. Testing sessionId + dict message...")
try:
    req = IncomingRequest(
        sessionId="test-123",
        message={"text": "Hello", "sender": "scammer", "timestamp": "2026-02-01T10:00:00Z"}
    )
    print(f"✅ Dict message accepted: {req.model_dump()}")
except Exception as e:
    print(f"❌ Failed: {e}")

# Test 5: Full format with Message object
print("\n5. Testing full format with Message object...")
try:
    req = IncomingRequest(
        sessionId="test-123",
        message=Message(
            sender="scammer",
            text="Hello",
            timestamp="2026-02-01T10:00:00Z"
        ),
        conversationHistory=[],
        metadata={"channel": "SMS"}
    )
    print(f"✅ Full format accepted: {req.model_dump()}")
except Exception as e:
    print(f"❌ Failed: {e}")

# Test 6: Minimal GUVI format
print("\n6. Testing minimal GUVI format (sessionId + message dict)...")
try:
    data = {"sessionId": "test-123", "message": {"text": "test"}}
    req = IncomingRequest(**data)
    print(f"✅ GUVI format accepted: {req.model_dump()}")
except Exception as e:
    print(f"❌ Failed: {e}")

# Test 7: Parse from JSON
print("\n7. Testing parse from JSON string...")
try:
    json_str = '{"sessionId": "test-456", "message": "test message"}'
    data = json.loads(json_str)
    req = IncomingRequest(**data)
    print(f"✅ JSON parsed successfully: {req.model_dump()}")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n" + "=" * 80)
print("All schema validation tests completed!")
