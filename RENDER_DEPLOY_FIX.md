# 🚀 Render Deployment Fix

## Problem

Your deployment timed out because **required environment variables are missing**.

## Error Analysis

```
==> Timed Out
==> Port scan timeout reached, no open ports detected
```

This means the app **crashed on startup** before it could open the port.

## Root Cause

The app requires `API_KEY` to start, but it wasn't set in Render's environment variables.

## ✅ Solution

### Step 1: Set Environment Variables in Render Dashboard

Go to your service in Render Dashboard → **Environment** tab → Add these:

**Required:**

```
API_KEY = your-secret-api-key-here
ANTHROPIC_API_KEY = your-anthropic-api-key
```

**Optional (but recommended):**

```
GOOGLE_API_KEY = your-google-api-key
```

### Step 2: Redeploy

After setting environment variables:

1. Go to **Manual Deploy** → Click **Deploy latest commit**
2. OR push the changes from this fix and it will auto-deploy

### Step 3: Verify Deployment

Once deployed, check:

```
https://your-app.onrender.com/health
```

Should return:

```json
{
  "status": "healthy",
  "service": "AI Agentic Honeypot System",
  "version": "1.0.0",
  "timestamp": "2026-02-11T15:30:00",
  "active_sessions": 0,
  "llm_provider": "anthropic"
}
```

## 📋 Changes Made

### 1. Updated [config.py](config.py)

- Made `API_KEY` have a default value (prevents crash if missing)
- App will start but show warning if not configured

### 2. Updated [render.yaml](render.yaml)

- Added `API_KEY` environment variable definition
- Added `ANTHROPIC_API_KEY` environment variable definition
- Both marked as `sync: false` (set in Render Dashboard)

### 3. Improved [main.py](main.py)

- Added detailed startup logging (Python version, port, config status)
- Added startup event handler (logs when ready to accept requests)
- Better diagnostics for troubleshooting

## 🎯 What to Expect

### Successful Deployment Logs

```
============================================================
AI AGENTIC HONEYPOT SYSTEM STARTING
Python version: 3.13.1
LLM Provider: anthropic
Host: 0.0.0.0
Port: 10000
API Key configured: Yes
============================================================
✅ All services initialized successfully
============================================================
🚀 APPLICATION READY - Port is open and accepting requests
📡 Health check: http://0.0.0.0:10000/health
============================================================
```

### Build Times

- Build: ~30 seconds
- Deploy: ~30 seconds
- **Total: ~1 minute** (not 15 minutes!)

## 🔍 Troubleshooting

### If deployment still fails:

1. **Check logs** in Render Dashboard → Logs tab
2. **Look for**:
   - "AI AGENTIC HONEYPOT SYSTEM STARTING" (app started)
   - "✅ All services initialized" (services loaded)
   - "🚀 APPLICATION READY" (port opened)

3. **If you see "API Key configured: NO"**:
   - Environment variable not set correctly
   - Go to Render Dashboard → Environment → Add `API_KEY`

4. **If app crashes before "🚀 APPLICATION READY"**:
   - Check if ANTHROPIC_API_KEY is missing
   - Check for Python dependency errors

## 📌 Important Notes

1. **Never commit API keys** to git - set them only in Render Dashboard
2. **Use different keys** for production vs development
3. **Monitor API usage** to avoid rate limits
4. **Check free tier limits** on Anthropic/Google

## 🚀 Quick Deploy Checklist

- [ ] Set `API_KEY` in Render Dashboard
- [ ] Set `ANTHROPIC_API_KEY` in Render Dashboard
- [ ] (Optional) Set `GOOGLE_API_KEY` in Render Dashboard
- [ ] Push latest changes (config.py, main.py, render.yaml)
- [ ] Wait for build (~30s)
- [ ] Verify `/health` endpoint works
- [ ] Test with a message request

## 🎉 After Successful Deploy

Your app will be available at:

```
https://your-app-name.onrender.com
```

Test it:

```bash
curl -X POST https://your-app-name.onrender.com/api/message \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{
    "sessionId": "test-session",
    "message": {
      "sender": "scammer",
      "text": "Urgent! Share your OTP to verify account",
      "timestamp": "2026-02-11T15:30:00Z"
    },
    "conversationHistory": [],
    "metadata": {
      "channel": "SMS",
      "language": "English",
      "locale": "IN"
    }
  }'
```

## 📱 Keep-Alive Cron Job

The cron job will run every 10 minutes to prevent cold starts:

```yaml
- type: cron
  name: honeypot-keep-alive
  schedule: "*/10 * * * *"
```

This keeps your service warm and fast! ⚡
