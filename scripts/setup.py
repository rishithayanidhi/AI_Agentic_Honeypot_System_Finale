#!/usr/bin/env python3
"""
Setup script for AI Agentic Honeypot System
This script helps you configure and test the system
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")


def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"❌ Python 3.9+ required. You have {version.major}.{version.minor}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def create_venv():
    """Create virtual environment"""
    print("\nCreating virtual environment...")
    if os.path.exists("venv"):
        print("✓ Virtual environment already exists")
        return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✓ Virtual environment created")
        return True
    except Exception as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False


def install_dependencies():
    """Install required packages"""
    print("\nInstalling dependencies...")
    
    # Determine pip path based on OS
    if sys.platform == "win32":
        pip_path = "venv\\Scripts\\pip"
    else:
        pip_path = "venv/bin/pip"
    
    try:
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        print("✓ Dependencies installed")
        return True
    except Exception as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def create_env_file():
    """Create .env file from template"""
    print("\nSetting up .env file...")
    
    if os.path.exists(".env"):
        response = input(".env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("✓ Using existing .env file")
            return True
    
    # Copy from example
    try:
        with open(".env.example", "r") as f:
            content = f.read()
        
        with open(".env", "w") as f:
            f.write(content)
        
        print("✓ .env file created from template")
        print("\n⚠️  IMPORTANT: Edit .env file and add your API keys!")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def configure_api_keys():
    """Interactive API key configuration"""
    print("\nAPI Key Configuration")
    print("-" * 60)
    
    # Read current .env
    env_content = {}
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_content[key] = value
    
    # Configure API_KEY
    print("\n1. System API Key")
    print("   This is the key users will use to authenticate with your API")
    current_api_key = env_content.get("API_KEY", "your-secret-api-key-here")
    api_key = input(f"   Enter API Key [{current_api_key}]: ").strip()
    if not api_key:
        api_key = current_api_key
    env_content["API_KEY"] = api_key
    
    # Configure LLM Provider
    print("\n2. LLM Provider")
    print("   Choose: 'openai' or 'anthropic'")
    current_provider = env_content.get("LLM_PROVIDER", "openai")
    provider = input(f"   Enter provider [{current_provider}]: ").strip().lower()
    if not provider:
        provider = current_provider
    env_content["LLM_PROVIDER"] = provider
    
    # Configure OpenAI
    if provider == "openai":
        print("\n3. OpenAI Configuration")
        current_key = env_content.get("OPENAI_API_KEY", "")
        if current_key and current_key != "your-openai-api-key-here":
            masked_key = current_key[:10] + "..." + current_key[-4:]
            openai_key = input(f"   Enter OpenAI API Key [{masked_key}]: ").strip()
            if not openai_key:
                openai_key = current_key
        else:
            openai_key = input("   Enter OpenAI API Key: ").strip()
        
        if openai_key:
            env_content["OPENAI_API_KEY"] = openai_key
        
        current_model = env_content.get("OPENAI_MODEL", "gpt-4-turbo-preview")
        model = input(f"   Enter model [{current_model}]: ").strip()
        if not model:
            model = current_model
        env_content["OPENAI_MODEL"] = model
    
    # Configure Anthropic
    elif provider == "anthropic":
        print("\n3. Anthropic Configuration")
        current_key = env_content.get("ANTHROPIC_API_KEY", "")
        if current_key and current_key != "your-anthropic-api-key-here":
            masked_key = current_key[:10] + "..." + current_key[-4:]
            anthropic_key = input(f"   Enter Anthropic API Key [{masked_key}]: ").strip()
            if not anthropic_key:
                anthropic_key = current_key
        else:
            anthropic_key = input("   Enter Anthropic API Key: ").strip()
        
        if anthropic_key:
            env_content["ANTHROPIC_API_KEY"] = anthropic_key
        
        current_model = env_content.get("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
        model = input(f"   Enter model [{current_model}]: ").strip()
        if not model:
            model = current_model
        env_content["ANTHROPIC_MODEL"] = model
    
    # Save to .env
    with open(".env", "w") as f:
        f.write("# API Configuration\n")
        f.write(f"API_KEY={env_content.get('API_KEY')}\n")
        f.write("PORT=8000\n")
        f.write("HOST=0.0.0.0\n\n")
        
        f.write("# LLM Provider\n")
        f.write(f"LLM_PROVIDER={env_content.get('LLM_PROVIDER')}\n\n")
        
        f.write("# OpenAI Configuration\n")
        f.write(f"OPENAI_API_KEY={env_content.get('OPENAI_API_KEY', 'your-openai-api-key-here')}\n")
        f.write(f"OPENAI_MODEL={env_content.get('OPENAI_MODEL', 'gpt-4-turbo-preview')}\n\n")
        
        f.write("# Anthropic Configuration\n")
        f.write(f"ANTHROPIC_API_KEY={env_content.get('ANTHROPIC_API_KEY', 'your-anthropic-api-key-here')}\n")
        f.write(f"ANTHROPIC_MODEL={env_content.get('ANTHROPIC_MODEL', 'claude-3-sonnet-20240229')}\n\n")
        
        f.write("# GUVI Callback\n")
        f.write("GUVI_CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult\n\n")
        
        f.write("# Session Configuration\n")
        f.write("SESSION_TIMEOUT_MINUTES=30\n")
        f.write("MAX_MESSAGES_PER_SESSION=50\n\n")
        
        f.write("# Redis (Optional)\n")
        f.write("REDIS_HOST=localhost\n")
        f.write("REDIS_PORT=6379\n")
        f.write("REDIS_DB=0\n")
        f.write("USE_REDIS=false\n")
    
    print("\n✓ Configuration saved to .env")
    return True


def print_next_steps():
    """Print next steps for the user"""
    print_header("Setup Complete!")
    
    print("Next steps:\n")
    print("1. Activate virtual environment:")
    if sys.platform == "win32":
        print("   venv\\Scripts\\activate\n")
    else:
        print("   source venv/bin/activate\n")
    
    print("2. Start the server:")
    print("   python main.py\n")
    
    print("3. Test the API:")
    print("   python tests/test_api.py\n")
    
    print("4. Access the API:")
    print("   http://localhost:8000\n")
    
    print("5. Read the documentation:")
    print("   README.md - Quick start guide")
    print("   DEPLOYMENT.md - Production deployment\n")
    
    print("For help, visit: https://github.com/yourusername/ai-honeypot\n")


def main():
    """Main setup function"""
    print_header("AI Agentic Honeypot System - Setup")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_venv():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        sys.exit(1)
    
    # Interactive configuration
    print("\nWould you like to configure API keys now?")
    response = input("Configure now? (Y/n): ")
    if response.lower() != 'n':
        configure_api_keys()
    else:
        print("\n⚠️  Remember to edit .env and add your API keys before running!")
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        sys.exit(1)
