"""
Toggle Fast Mode ON/OFF
Quick script to switch between testing and production modes
"""
import re
from pathlib import Path


def get_current_mode():
    """Read current FAST_MODE setting from config.py"""
    config_path = Path('config.py')
    content = config_path.read_text()
    
    match = re.search(r'FAST_MODE:\s*bool\s*=\s*(True|False)', content)
    if match:
        return match.group(1) == 'True'
    return None


def toggle_mode():
    """Toggle FAST_MODE in config.py"""
    config_path = Path('config.py')
    content = config_path.read_text()
    
    # Find current setting
    current = get_current_mode()
    if current is None:
        print("❌ Could not find FAST_MODE in config.py")
        return False
    
    # Toggle
    new_mode = not current
    
    # Replace in file
    if current:
        content = content.replace('FAST_MODE: bool = True', 'FAST_MODE: bool = False')
    else:
        content = content.replace('FAST_MODE: bool = False', 'FAST_MODE: bool = True')
    
    config_path.write_text(content)
    
    print("=" * 60)
    print("FAST_MODE Toggle")
    print("=" * 60)
    print(f"Previous: {'ENABLED ⚡' if current else 'DISABLED 🐢'}")
    print(f"New:      {'ENABLED ⚡' if new_mode else 'DISABLED 🐢'}")
    print()
    
    if new_mode:
        print("✅ FAST_MODE ENABLED")
        print("   • Instant responses (0.5-3s)")
        print("   • No throttling delays")
        print("   • Perfect for GUVI testing")
        print("   • May hit rate limits faster")
    else:
        print("✅ FAST_MODE DISABLED")
        print("   • Rate limiting enabled")
        print("   • 12s between requests")
        print("   • Better for production")
        print("   • Protects API quotas")
    
    print()
    print("⚠️  Restart your service for changes to take effect:")
    print("   python main.py")
    print("=" * 60)
    
    return True


def show_status():
    """Show current FAST_MODE status"""
    current = get_current_mode()
    
    print("=" * 60)
    print("FAST_MODE Status")
    print("=" * 60)
    
    if current is None:
        print("❌ Could not determine FAST_MODE status")
        return
    
    if current:
        print("⚡ FAST_MODE: ENABLED")
        print()
        print("What this means:")
        print("  • Throttling: DISABLED")
        print("  • Cooldowns: IGNORED")
        print("  • Timeout: 3 seconds")
        print("  • Retries: 1 model only")
        print("  • Response time: 0.5-3s")
        print()
        print("✅ Perfect for GUVI testing and demos")
        print("⚠️  May hit rate limits in high traffic")
    else:
        print("🐢 FAST_MODE: DISABLED")
        print()
        print("What this means:")
        print("  • Throttling: ENABLED (12s minimum)")
        print("  • Cooldowns: RESPECTED")
        print("  • Timeout: 20 seconds")
        print("  • Retries: All 6 models")
        print("  • Response time: 14-20s")
        print()
        print("✅ Better for production with high traffic")
        print("⚠️  Slower responses but quota-safe")
    
    print()
    print("To toggle: python toggle_fast_mode.py --toggle")
    print("=" * 60)


def main():
    import sys
    
    if '--toggle' in sys.argv or '-t' in sys.argv:
        toggle_mode()
    else:
        show_status()


if __name__ == "__main__":
    main()
