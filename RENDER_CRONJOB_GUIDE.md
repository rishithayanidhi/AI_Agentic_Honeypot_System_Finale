# 🚀 Render Deployment with Cron Jobs (100% Free)

**Perfect for GUVI Hackathon!** Stay completely free while preventing cold starts.

---

## ✅ What This Does

**Problem**: Render free tier sleeps after 15 minutes of inactivity (30-60s to wake up)

**Solution**: Cron job pings your app every 10 minutes to keep it awake

**Result**:

- ✅ 100% Free
- ✅ No cold starts during GUVI evaluation
- ✅ Fast response times (300-800ms warm)

---

## 📋 Setup Steps (10 Minutes)

### Step 1: Push to GitHub

```powershell
git add .
git commit -m "Add Render cron job configuration"
git push origin main
```

### Step 2: Deploy to Render

1. Go to **https://render.com** → Sign up/Login
2. Click **"New+"** → **"Web Service"**
3. Connect your GitHub repository
4. Select your repo: `AI Scammer Detection`

### Step 3: Configure Web Service

**Build & Deploy:**

- **Name**: `ai-honeypot-system`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Instance Type**: `Free`

**Environment Variables** (click "Advanced"):

```
ANTHROPIC_API_KEY=your-anthropic-key-here
API_KEY=guvi-secret-key-12345
LLM_PROVIDER=anthropic
ANTHROPIC_MODEL=claude-haiku-4.5-20250110
```

Click **"Create Web Service"** → Wait for deployment (3-5 minutes)

### Step 4: Add Cron Job (Keep Alive)

1. In Render dashboard, click **"New+"** → **"Cron Job"**
2. Use same repository
3. Configure:

**Cron Job Settings:**

- **Name**: `honeypot-keep-alive`
- **Runtime**: `Python 3`
- **Build Command**: `pip install requests`
- **Command**: `python scripts/keep_alive.py`
- **Schedule**: `*/10 * * * *` (Every 10 minutes)

**Environment Variable** (Important!):

```
RENDER_EXTERNAL_URL=https://your-web-service-url.onrender.com
```

Replace with YOUR web service URL from Step 3!

4. Click **"Create Cron Job"**

---

## 🎯 How It Works

```
Your App (Render Web Service)
        ↑
        │ HTTP GET /health
        │ Every 10 minutes
        │
Cron Job (Keep Alive Script)
```

**Timeline:**

- **0:00** - Cron job pings `/health`
- **0:10** - Cron job pings `/health`
- **0:20** - Cron job pings `/health`
- **Result**: App never sleeps! ✅

---

## ✅ Verify Setup

### Test Your Web Service

```powershell
# Test health endpoint
curl https://your-app-name.onrender.com/health

# Expected response:
# {"status":"healthy","service":"AI Agentic Honeypot System","version":"1.0.0"}
```

### Test API Endpoint

```powershell
curl -X POST https://your-app-name.onrender.com/api/message `
  -H "x-api-key: guvi-secret-key-12345" `
  -H "Content-Type: application/json" `
  -d '{
    "sessionId": "test-001",
    "message": {
      "sender": "scammer",
      "text": "Your account is blocked. Share OTP.",
      "timestamp": "2026-02-11T10:00:00Z"
    }
  }'
```

### Check Cron Job Logs

1. Go to Render → Your Cron Job
2. Click "Logs"
3. You should see:

```
🤖 Render Keep-Alive Cron Job
🔔 Pinging: https://your-app.onrender.com/health
✅ Service is alive! Status: 200
```

---

## 📊 Performance Comparison

### Without Cron Job ❌

- First request: **30-60 seconds** (cold start)
- Subsequent: **300-800ms**
- Problem: GUVI checker may timeout

### With Cron Job ✅

- All requests: **300-800ms** (always warm)
- No cold starts during evaluation period
- Perfect for automated testing

---

## 🎯 For GUVI Submission

**Your Endpoint:**

```
URL: https://your-app-name.onrender.com/api/message
Method: POST
Headers:
  x-api-key: guvi-secret-key-12345
  Content-Type: application/json
```

**Sample Request:**

```json
{
  "sessionId": "guvi-eval-001",
  "message": {
    "sender": "scammer",
    "text": "Your account is blocked. Share OTP immediately.",
    "timestamp": "2026-02-11T12:00:00Z"
  },
  "conversationHistory": [],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

---

## 🔧 Troubleshooting

### Cron Job Not Running?

**Check RENDER_EXTERNAL_URL:**

```powershell
# In Render dashboard → Cron Job → Environment
# Make sure RENDER_EXTERNAL_URL is set to your web service URL
```

**Check Schedule:**

```
*/10 * * * *  ✅ Correct (every 10 minutes)
10 * * * *    ❌ Wrong (only at :10 past each hour)
```

### Still Getting Cold Starts?

**Reduce cron frequency:**

```
*/5 * * * *   # Every 5 minutes (more pings)
```

**Or run multiple cron jobs:**

- One at `:00, :10, :20, :30, :40, :50`
- One at `:05, :15, :25, :35, :45, :55`

### App Still Sleeping?

**Check if cron job is actually running:**

1. Render → Cron Job → Logs
2. Should see new entries every 10 minutes
3. If not, check build command succeeded

---

## 💰 Cost Analysis

**Render Free Tier:**

- ✅ Web Service: Free (750 hours/month)
- ✅ Cron Job: Free (unlimited)
- ✅ Total Cost: **$0/month** 🎉

**Comparison:**

- Railway: $5/month (faster but paid)
- Render + Cron: $0/month (free, good performance)

---

## ⏰ Cron Schedule Examples

```bash
# Every 10 minutes (recommended)
*/10 * * * *

# Every 5 minutes (aggressive)
*/5 * * * *

# Every 15 minutes (conservative)
*/15 * * * *

# Only during business hours (9 AM - 6 PM UTC)
*/10 9-18 * * *

# Only on weekdays during evaluation
*/10 * * * 1-5
```

---

## 📈 Best Practices

1. **Set up 24 hours before GUVI evaluation**
   - Ensures everything is working
   - Gives time to troubleshoot

2. **Monitor cron job logs**
   - Check they're running every 10 minutes
   - Verify 200 OK responses

3. **Test response times**

   ```powershell
   python test_deployment_speed.py
   ```

   - Should show warm responses <1s

4. **Keep app warm during evaluation window**
   - Reduce interval to every 5 minutes if needed
   - Can temporarily add more cron jobs

---

## 🎉 Deployment Checklist

- [ ] Web service deployed to Render
- [ ] Environment variables set
- [ ] Health endpoint returns 200
- [ ] Cron job created
- [ ] RENDER_EXTERNAL_URL set in cron job
- [ ] Cron job running (check logs)
- [ ] No cold starts confirmed (test multiple times)
- [ ] Response times <1s
- [ ] URL + API key documented for GUVI

---

## 🚀 Alternative: Uptime Monitoring (Bonus)

**Add UptimeRobot for extra reliability:**

1. Go to **https://uptimerobot.com** (free)
2. Add new monitor:
   - Type: HTTP(s)
   - URL: `https://your-app.onrender.com/health`
   - Interval: 5 minutes
3. Now you have **two systems** keeping your app warm! 🔥

---

## 📝 Quick Reference

**Web Service URL**: `https://your-app-name.onrender.com`

**API Endpoint**: `https://your-app-name.onrender.com/api/message`

**API Key**: `guvi-secret-key-12345`

**Cron Schedule**: `*/10 * * * *` (every 10 minutes)

**Expected Performance**:

- Warm response: 300-800ms ✅
- Cold start: Never (cron keeps it warm) ✅

---

## ✅ Success Indicators

You're ready for GUVI when:

1. ✅ Health endpoint responds in <1s
2. ✅ API endpoint works correctly
3. ✅ Cron job logs show regular pings
4. ✅ No 30-60s delays on any request
5. ✅ Test script shows GOOD grade

---

**Deploy with confidence! Your FREE setup is production-ready.** 🎉
