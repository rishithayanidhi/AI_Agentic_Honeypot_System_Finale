#!/bin/bash
# Railway Quick Deploy Script
# Run this after: railway login

echo "🚀 Deploying to Railway..."

# Initialize Railway project
railway init

# Link to new project
railway link

# Set environment variables
railway variables set LLM_PROVIDER=anthropic
railway variables set ANTHROPIC_MODEL=claude-haiku-4.5-20250110
railway variables set API_KEY=guvi-secret-key-12345
railway variables set ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

# Deploy
railway up

echo "✅ Deployment complete!"
echo "Get your URL: railway domain"
