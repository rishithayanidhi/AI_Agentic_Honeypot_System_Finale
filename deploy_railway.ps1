# Railway Quick Deploy (Windows PowerShell)
# Run this after: railway login

Write-Host "🚀 Deploying to Railway..." -ForegroundColor Green

# Initialize Railway project
railway init

# Link to new project
railway link

# Set environment variables
railway variables set LLM_PROVIDER=anthropic
railway variables set ANTHROPIC_MODEL=claude-haiku-4.5-20250110
railway variables set API_KEY=guvi-secret-key-12345
railway variables set ANTHROPIC_API_KEY=$env:ANTHROPIC_API_KEY

# Deploy
railway up

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "Get your URL: railway domain"
