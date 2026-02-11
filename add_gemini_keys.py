"""
Add Multiple Gemini API Keys
This script helps you add and test multiple Gemini API keys for better rate limit handling
"""
import os
import sys
from pathlib import Path
from google import genai


def test_gemini_key(api_key: str, key_number: int) -> bool:
    """Test if a Gemini API key is valid"""
    try:
        print(f"  Testing key {key_number} (...{api_key[-4:]}): ", end="")
        client = genai.Client(api_key=api_key)
        
        # Try a simple request
        response = client.models.generate_content(
            model='models/gemini-2.5-flash',
            contents='Say "OK" if you can read this.',
            config={'maxOutputTokens': 10}
        )
        
        if response and hasattr(response, 'text'):
            print("✅ Valid")
            return True
        else:
            print("❌ Invalid response")
            return False
            
    except Exception as e:
        error_msg = str(e)
        if "API key not valid" in error_msg or "authentication" in error_msg.lower():
            print(f"❌ Invalid API key")
        elif "429" in error_msg or "quota" in error_msg.lower():
            print(f"⚠️  Already at quota limit (but key is valid)")
            return True
        else:
            print(f"❌ Error: {error_msg[:50]}")
        return False


def update_env_file(keys: dict):
    """Update .env file with API keys"""
    env_path = Path('.env')
    
    if not env_path.exists():
        print("❌ .env file not found")
        return False
    
    # Read existing .env
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Update or add keys
    updated_lines = []
    keys_written = set()
    
    for line in lines:
        written = False
        for key_name, key_value in keys.items():
            if line.startswith(f"{key_name}="):
                updated_lines.append(f"{key_name}={key_value}\n")
                keys_written.add(key_name)
                written = True
                break
        
        if not written:
            updated_lines.append(line)
    
    # Add any keys that weren't in the file
    for key_name, key_value in keys.items():
        if key_name not in keys_written:
            updated_lines.append(f"{key_name}={key_value}\n")
    
    # Write back
    with open(env_path, 'w') as f:
        f.writelines(updated_lines)
    
    print("✅ .env file updated")
    return True


def main():
    print("=" * 70)
    print("Gemini API Key Configuration - Add Multiple Keys for Rate Limiting")
    print("=" * 70)
    print()
    print("Benefits of multiple API keys:")
    print("  - Each key has separate rate limits (5 req/min for free tier)")
    print("  - System rotates between keys automatically")
    print("  - Better availability and fewer cooldowns")
    print()
    print("Get free API keys at: https://ai.google.dev/")
    print()
    
    # Collect API keys
    keys = {}
    key_number = 1
    
    while True:
        key_var = f"GOOGLE_API_KEY" if key_number == 1 else f"GOOGLE_API_KEY_{key_number}"
        
        print(f"\nEnter {key_var} (or press Enter to finish):")
        api_key = input("  API Key: ").strip()
        
        if not api_key:
            if key_number == 1:
                print("❌ You must provide at least one API key")
                continue
            else:
                break
        
        # Test the key
        if test_gemini_key(api_key, key_number):
            keys[key_var] = api_key
            key_number += 1
            
            if key_number > 4:
                print("\n✅ Maximum of 4 keys configured")
                break
        else:
            print("❌ Key failed validation, please try again")
    
    if not keys:
        print("\n❌ No valid keys provided")
        return
    
    print(f"\n✅ Configured {len(keys)} valid Gemini API key(s)")
    print()
    
    # Update .env file
    print("Updating .env file...")
    if update_env_file(keys):
        print()
        print("=" * 70)
        print("✅ Configuration complete!")
        print()
        print("Next steps:")
        print("  1. Restart your application to load new keys")
        print("  2. Run 'python monitor_api_status.py' to verify setup")
        print("  3. System will now rotate between keys automatically")
        print("=" * 70)
    else:
        print("\n❌ Failed to update .env file")
        print("Please manually add these keys to your .env file:")
        for key_name, key_value in keys.items():
            print(f"  {key_name}={key_value}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
