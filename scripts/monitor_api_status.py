"""
Monitor API Status and Cooldowns
Run this script to check the status of all LLM providers and cooldowns
"""
import sys
from datetime import datetime
from src.services.ai_agent import AIAgent
from config import settings


def format_time_remaining(cooldown_time):
    """Format remaining cooldown time"""
    if datetime.now() >= cooldown_time:
        return "✅ Available"
    remaining = (cooldown_time - datetime.now()).total_seconds()
    if remaining > 3600:
        return f"🔴 Cooldown: {remaining/3600:.1f} hours"
    elif remaining > 60:
        return f"🟡 Cooldown: {remaining/60:.1f} minutes"
    else:
        return f"🟠 Cooldown: {remaining:.0f} seconds"


def main():
    print("=" * 60)
    print("AI Scammer Detection - API Status Monitor")
    print("=" * 60)
    print()
    
    # Initialize agent
    agent = AIAgent()
    
    # Provider Status
    print("📊 Provider Status:")
    print("-" * 60)
    for provider in ['gemini', 'anthropic']:
        if provider in agent.available_providers:
            if provider in agent.provider_cooldowns:
                status = format_time_remaining(agent.provider_cooldowns[provider])
            else:
                status = "✅ Available"
            print(f"  {provider.upper()}: {status}")
        else:
            print(f"  {provider.upper()}: ❌ Not configured")
    print()
    
    # Gemini Keys Status
    if agent.gemini_clients:
        print(f"🔑 Gemini API Keys: {len(agent.gemini_clients)} configured")
        print(f"  Current key index: {agent.gemini_key_index + 1}")
        print()
    
    # Model Cooldowns
    if agent.model_cooldowns:
        print("🤖 Model Cooldowns:")
        print("-" * 60)
        for model, cooldown_time in agent.model_cooldowns.items():
            status = format_time_remaining(cooldown_time)
            model_short = model.replace('models/', '')
            print(f"  {model_short}: {status}")
        print()
    else:
        print("✅ No models in cooldown")
        print()
    
    # Configuration
    print("⚙️  Rate Limiting Configuration:")
    print("-" * 60)
    print(f"  Min Request Interval: {settings.MIN_REQUEST_INTERVAL}s")
    print(f"  Default Retry Delay: {settings.DEFAULT_RETRY_DELAY}s")
    print(f"  Quota Exhausted Cooldown: {settings.QUOTA_EXHAUSTED_COOLDOWN}s ({settings.QUOTA_EXHAUSTED_COOLDOWN/3600:.1f}h)")
    print(f"  Billing Error Cooldown: {settings.BILLING_ERROR_COOLDOWN}s ({settings.BILLING_ERROR_COOLDOWN/3600:.1f}h)")
    print()
    
    # Recommendations
    print("💡 Recommendations:")
    print("-" * 60)
    
    has_issues = False
    
    if 'gemini' in agent.provider_cooldowns:
        remaining = (agent.provider_cooldowns['gemini'] - datetime.now()).total_seconds()
        if remaining > 3000:  # More than 50 minutes
            print("  ⚠️  Gemini has long cooldown - daily quota likely exhausted")
            print("     Consider adding more API keys or upgrading your plan")
            has_issues = True
    
    if 'anthropic' in agent.provider_cooldowns:
        remaining = (agent.provider_cooldowns['anthropic'] - datetime.now()).total_seconds()
        if remaining > 3000:
            print("  ⚠️  Anthropic has long cooldown - likely billing issue")
            print("     Check your Anthropic account billing and credits")
            has_issues = True
    
    if len(agent.gemini_clients) < 2:
        print("  💡 Consider adding multiple Gemini API keys for better availability")
        print("     Set GOOGLE_API_KEY_2, GOOGLE_API_KEY_3, etc. in .env")
    
    if not agent.available_providers:
        print("  ❌ NO PROVIDERS AVAILABLE - System running on fallback only!")
        has_issues = True
    
    if not has_issues and not agent.model_cooldowns and not agent.provider_cooldowns:
        print("  ✅ All systems operational!")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
