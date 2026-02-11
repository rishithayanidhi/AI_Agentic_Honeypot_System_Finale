# Quick Live Scammer Test (PowerShell)
# Simple script to test your deployed system with realistic scammer messages

# ===================================
# CONFIGURATION - UPDATE THESE!
# ===================================

$BASE_URL = "https://ai-agentic-honeypot-system-finale.onrender.com"  # ⚠️ CHANGE THIS!
$API_KEY = "honeypot-secret-2026"

# ===================================
# Test Scammer Messages
# ===================================

$scammerMessages = @(
    "URGENT: Your bank account will be blocked in 2 hours!",
    "I am from SBI security. Share OTP immediately: 123456",
    "Transfer ₹1 to verify: security@paytm",
    "Click this link to update KYC: bit.ly/kyc-urgent",
    "Congratulations! You won ₹25 lakhs. Pay ₹5000 fee to claim."
)

# ===================================
# Functions
# ===================================

function Test-SingleMessage {
    param($message, $messageNumber = 1)
    
    $sessionId = "test-$(Get-Date -Format 'yyyyMMddHHmmss')"
    $timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    
    $body = @{
        sessionId = $sessionId
        message = @{
            sender = "scammer"
            text = $message
            timestamp = $timestamp
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
    
    Write-Host "`n📤 Message #$messageNumber (Scammer):" -ForegroundColor Cyan
    Write-Host "   $message" -ForegroundColor Gray
    Write-Host "   Sending... " -NoNewline
    
    try {
        $startTime = Get-Date
        $response = Invoke-RestMethod -Uri "$BASE_URL/api/message" -Method POST -Body $body -Headers $headers -TimeoutSec 30
        $duration = ((Get-Date) - $startTime).TotalSeconds
        
        Write-Host "✅ ($([math]::Round($duration, 2))s)" -ForegroundColor Green
        
        # Show agent response
        if ($response.agentResponse) {
            Write-Host "`n💬 Agent Response:" -ForegroundColor Yellow
            Write-Host "   $($response.agentResponse)" -ForegroundColor Gray
        }
        
        # Show detection
        Write-Host "`n🔍 Detection:" -ForegroundColor Magenta
        Write-Host "   Scam Detected: $($response.scamDetected)" -ForegroundColor $(if($response.scamDetected){"Red"}else{"Green"})
        if ($response.agentNotes) {
            Write-Host "   Type: $($response.agentNotes)" -ForegroundColor Gray
        }
        
        # Show intelligence
        $intel = $response.extractedIntelligence
        if ($intel.bankAccounts -or $intel.upiIds -or $intel.phishingLinks -or $intel.phoneNumbers) {
            Write-Host "`n🎯 Intelligence Extracted:" -ForegroundColor Green
            if ($intel.bankAccounts) { Write-Host "   💳 Bank Accounts: $($intel.bankAccounts -join ', ')" }
            if ($intel.upiIds) { Write-Host "   💰 UPI IDs: $($intel.upiIds -join ', ')" }
            if ($intel.phishingLinks) { Write-Host "   🔗 Links: $($intel.phishingLinks -join ', ')" }
            if ($intel.phoneNumbers) { Write-Host "   📱 Phones: $($intel.phoneNumbers -join ', ')" }
        }
        
        return $response
        
    } catch {
        Write-Host "❌ Error" -ForegroundColor Red
        Write-Host "   $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function Test-Conversation {
    param($messages)
    
    Write-Host "`n" + ("="*80) -ForegroundColor Cyan
    Write-Host "🎭 TESTING MULTI-TURN SCAMMER CONVERSATION" -ForegroundColor Cyan
    Write-Host ("="*80) -ForegroundColor Cyan
    
    $results = @()
    $messageNum = 1
    
    foreach ($msg in $messages) {
        $result = Test-SingleMessage -message $msg -messageNumber $messageNum
        $results += $result
        $messageNum++
        
        if ($result -and $result.sessionComplete) {
            Write-Host "`n⛔ Session ended by agent (safety)" -ForegroundColor Red
            break
        }
        
        if ($messageNum -le $messages.Count) {
            Write-Host "`n⏳ Waiting 2s before next message..." -ForegroundColor Gray
            Start-Sleep -Seconds 2
        }
    }
    
    # Summary
    Write-Host "`n" + ("="*80) -ForegroundColor Green
    Write-Host "📊 CONVERSATION SUMMARY" -ForegroundColor Green
    Write-Host ("="*80) -ForegroundColor Green
    
    $successCount = ($results | Where-Object { $_ -ne $null }).Count
    Write-Host "✅ Messages Sent: $($messages.Count)"
    Write-Host "✅ Responses Received: $successCount"
    
    # Collect all intelligence
    $allBankAccounts = @()
    $allUpiIds = @()
    $allLinks = @()
    $allPhones = @()
    
    foreach ($result in $results) {
        if ($result) {
            $intel = $result.extractedIntelligence
            if ($intel.bankAccounts) { $allBankAccounts += $intel.bankAccounts }
            if ($intel.upiIds) { $allUpiIds += $intel.upiIds }
            if ($intel.phishingLinks) { $allLinks += $intel.phishingLinks }
            if ($intel.phoneNumbers) { $allPhones += $intel.phoneNumbers }
        }
    }
    
    $allBankAccounts = $allBankAccounts | Select-Object -Unique
    $allUpiIds = $allUpiIds | Select-Object -Unique
    $allLinks = $allLinks | Select-Object -Unique
    $allPhones = $allPhones | Select-Object -Unique
    
    Write-Host "`n🎯 Total Intelligence Collected:" -ForegroundColor Yellow
    Write-Host "   💳 Bank Accounts: $($allBankAccounts.Count)"
    Write-Host "   💰 UPI IDs: $($allUpiIds.Count)"
    Write-Host "   🔗 Links: $($allLinks.Count)"
    Write-Host "   📱 Phones: $($allPhones.Count)"
    
    if ($allBankAccounts -or $allUpiIds -or $allLinks -or $allPhones) {
        Write-Host "`n📋 Extracted Items:" -ForegroundColor Green
        if ($allBankAccounts) { Write-Host "   Accounts: $($allBankAccounts -join ', ')" }
        if ($allUpiIds) { Write-Host "   UPI IDs: $($allUpiIds -join ', ')" }
        if ($allLinks) { Write-Host "   Links: $($allLinks -join ', ')" }
        if ($allPhones) { Write-Host "   Phones: $($allPhones -join ', ')" }
    }
}

# ===================================
# Main Script
# ===================================

Write-Host "="*80 -ForegroundColor Cyan
Write-Host "🤖 LIVE SCAMMER CONVERSATION TESTER" -ForegroundColor Cyan
Write-Host "="*80 -ForegroundColor Cyan
Write-Host "Target: $BASE_URL" -ForegroundColor Gray
Write-Host "API Key: $($API_KEY.Substring(0, [Math]::Min(20, $API_KEY.Length)))..." -ForegroundColor Gray

# Check configuration
if ($BASE_URL -like "*your-app-name*") {
    Write-Host "`n❌ ERROR: Please update BASE_URL with your actual deployment URL!" -ForegroundColor Red
    Write-Host "   Edit this file and change BASE_URL at the top" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n📋 What would you like to test?" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Quick Test (1 message)" -ForegroundColor White
Write-Host "2. Full Conversation (5 messages)" -ForegroundColor White
Write-Host "3. Custom Message" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Select (1-3)"

switch ($choice) {
    "1" {
        Write-Host "`n🧪 Quick Test - Single Message" -ForegroundColor Cyan
        Test-SingleMessage -message $scammerMessages[0] -messageNumber 1
    }
    
    "2" {
        Test-Conversation -messages $scammerMessages
    }
    
    "3" {
        $customMsg = Read-Host "`nEnter custom scammer message"
        if ($customMsg) {
            Test-SingleMessage -message $customMsg -messageNumber 1
        }
    }
    
    default {
        Write-Host "`n❌ Invalid choice!" -ForegroundColor Red
    }
}

Write-Host "`n✅ Testing Complete!" -ForegroundColor Green
Write-Host ""
