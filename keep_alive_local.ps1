# Keep Render App Warm - Local Windows Task Scheduler
# Alternative to Render's cron job - runs on your computer
# Use this temporarily during GUVI evaluation if needed

$URL = "https://your-app-name.onrender.com/health"  # Replace with your Render URL
$API_KEY = "guvi-secret-key-12345"

Write-Host "🤖 Keep-Alive Script Started" -ForegroundColor Green
Write-Host "Pinging: $URL every 5 minutes..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

$count = 1

while ($true) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    try {
        Write-Host "[$timestamp] Ping #$count - " -NoNewline
        
        $response = Invoke-WebRequest -Uri $URL -Method GET -TimeoutSec 10
        
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Alive (200 OK)" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Status: $($response.StatusCode)" -ForegroundColor Yellow
        }
        
        $count++
        
    } catch {
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Wait 5 minutes (300 seconds)
    Start-Sleep -Seconds 300
}
