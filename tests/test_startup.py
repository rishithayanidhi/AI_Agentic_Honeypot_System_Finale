"""
Test startup to ensure app can start without errors
"""
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

print("=" * 70)
print("🧪 TESTING APP STARTUP")
print("=" * 70)

try:
    print("\n1️⃣ Testing config loading...")
    from config import settings
    print(f"   ✅ Config loaded")
    print(f"   - API_KEY: {'SET' if settings.API_KEY != 'CHANGE_ME_IN_PRODUCTION' else 'DEFAULT (not configured)'}")
    print(f"   - LLM_PROVIDER: {settings.LLM_PROVIDER}")
    print(f"   - HOST: {settings.HOST}")
    print(f"   - PORT: {settings.PORT}")
    
    print("\n2️⃣ Testing FastAPI app import...")
    from main import app
    print(f"   ✅ App imported successfully")
    print(f"   - Routes: {len(app.routes)}")
    
    print("\n3️⃣ Testing services initialization...")
    from main import scam_detector, ai_agent, intelligence_extractor
    print(f"   ✅ All services initialized")
    
    print("\n4️⃣ Testing route availability...")
    route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
    print(f"   ✅ Available routes:")
    for path in sorted(route_paths):
        print(f"      - {path}")
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED - App should start successfully!")
    print("=" * 70)
    print("\n🚀 To start the server:")
    print("   uvicorn main:app --host 0.0.0.0 --port 8000")
    print("\n📡 Then test health endpoint:")
    print("   curl http://localhost:8000/health")
    print("=" * 70)
    
except Exception as e:
    print("\n" + "=" * 70)
    print("❌ ERROR DURING STARTUP TEST")
    print("=" * 70)
    print(f"\nError: {e}")
    print(f"\nType: {type(e).__name__}")
    
    import traceback
    print("\nFull traceback:")
    print(traceback.format_exc())
    
    print("\n" + "=" * 70)
    print("🔍 TROUBLESHOOTING")
    print("=" * 70)
    print("\n1. Check if .env file exists and has required variables:")
    print("   API_KEY=your-key")
    print("   ANTHROPIC_API_KEY=your-anthropic-key")
    print("\n2. Check if all dependencies are installed:")
    print("   pip install -r requirements.txt")
    print("\n3. Check Python version (requires 3.9+):")
    print(f"   Current: {sys.version}")
    print("=" * 70)
    
    sys.exit(1)
