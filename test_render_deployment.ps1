# Test Your Render Deployment
# Replace YOUR_RENDER_URL with your actual Render URL

Write-Host "🧪 Testing Render Deployment..." -ForegroundColor Green
Write-Host ""

# REPLACE THIS with your actual Render URL
$RENDER_URL = "https://your-app-name.onrender.com"  # ⚠️ CHANGE THIS!
$API_KEY = "guvi-secret-key-12345"

Write-Host "URL: $RENDER_URL" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health Check
Write-Host "1️⃣ Testing Health Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$RENDER_URL/health" -Method GET -TimeoutSec 30
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ Health check passed!" -ForegroundColor Green
        Write-Host "   Response: $($response.Content)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   ⚠️  This is normal if app is still waking up (wait 30-60s)" -ForegroundColor Yellow
}

Write-Host ""
Start-Sleep -Seconds 2

# Test 2: API Endpoint
Write-Host "2️⃣ Testing API Endpoint..." -ForegroundColor Yellow
try {
    $body = @{
        sessionId = "test-001"
        message = @{
            sender = "scammer"
            text = "Your account is blocked. Share OTP immediately."
            timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
        }
        conversationHistory = @()
        metadata = @{
            channel = "SMS"
            language = "English"
            locale = "IN"
        }
    } | ConvertTo-Json -Depth 10

    $headers = @{
        "x-api-key" = $API_KEY
        "Content-Type" = "application/json"
    }

    Write-Host "   Sending request (may take 3-5s for LLM)..." -ForegroundColor Gray
    $response = Invoke-WebRequest -Uri "$RENDER_URL/api/message" -Method POST -Body $body -Headers $headers -TimeoutSec 30
    
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ API endpoint works!" -ForegroundColor Green
        $data = $response.Content | ConvertFrom-Json
        Write-Host "   Scam Detected: $($data.scamDetected)" -ForegroundColor Cyan
        Write-Host "   Response: $($data.agentResponse.Substring(0, [Math]::Min(100, $data.agentResponse.Length)))..." -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Gray
Write-Host "✅ Testing Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. If health check works but API fails, check your ANTHROPIC_API_KEY in Render dashboard"
Write-Host "2. Set up cron job to keep app warm (see instructions below)"
Write-Host "3. Submit URL to GUVI: $RENDER_URL/api/message"
