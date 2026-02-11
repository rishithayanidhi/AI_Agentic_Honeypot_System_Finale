"""
Local Keep-Alive Script (Python version)
Alternative to running on your computer if Render cron job doesn't work
"""

import requests
import time
from datetime import datetime
import sys

# CONFIGURE THIS
SERVICE_URL = "https://your-app-name.onrender.com"  # Replace with your Render URL
HEALTH_ENDPOINT = "/health"
PING_INTERVAL = 300  # 5 minutes (in seconds)

def ping_service():
    """Ping the service to keep it alive"""
    url = f"{SERVICE_URL}{HEALTH_ENDPOINT}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        print(f"[{timestamp}] Pinging: {url} ... ", end="", flush=True)
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Alive (200 OK)")
            return True
        else:
            print(f"⚠️  Status: {response.status_code}")
            return False
            
    except requests.Timeout:
        print("❌ Timeout (service may be waking up)")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Main loop - ping service every N minutes"""
    
    if "your-app-name" in SERVICE_URL:
        print("❌ ERROR: Please update SERVICE_URL in this script!")
        print("   Replace 'your-app-name' with your actual Render app name")
        sys.exit(1)
    
    print("=" * 60)
    print("🤖 Local Keep-Alive Script")
    print("=" * 60)
    print(f"Service: {SERVICE_URL}")
    print(f"Interval: Every {PING_INTERVAL//60} minutes")
    print(f"Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    ping_count = 1
    
    try:
        while True:
            print(f"\n🔔 Ping #{ping_count}")
            ping_service()
            ping_count += 1
            
            print(f"⏳ Waiting {PING_INTERVAL//60} minutes until next ping...")
            time.sleep(PING_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n✋ Stopped by user")
        print(f"Total pings sent: {ping_count - 1}")
        sys.exit(0)


if __name__ == "__main__":
    main()
