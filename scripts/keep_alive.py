"""
Keep Alive Script for Render Cron Job
Pings the health endpoint every 10 minutes to prevent cold starts
"""

import requests
import os
import time
from datetime import datetime

# Get the service URL from environment variable or use default
SERVICE_URL = os.getenv("RENDER_EXTERNAL_URL", "")
HEALTH_ENDPOINT = "/health"

def ping_health():
    """Ping the health endpoint to keep service alive"""
    
    if not SERVICE_URL:
        print("⚠️  RENDER_EXTERNAL_URL not set. Skipping keep-alive ping.")
        return False
    
    url = f"{SERVICE_URL}{HEALTH_ENDPOINT}"
    
    try:
        print(f"🔔 [{datetime.now().isoformat()}] Pinging: {url}")
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Service is alive! Status: {response.status_code}")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            return False
            
    except requests.Timeout:
        print(f"❌ Timeout after 10 seconds - service may be waking up")
        return False
        
    except requests.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🤖 Render Keep-Alive Cron Job")
    print("=" * 60)
    
    success = ping_health()
    
    if success:
        print("\n✅ Keep-alive successful!")
        exit(0)
    else:
        print("\n⚠️  Keep-alive failed (this is normal for first run)")
        exit(0)  # Don't fail the cron job
