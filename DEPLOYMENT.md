# 🚀 Deployment Guide - AI Scammer Detection Honeypot

**Recommendation**: Use Railway for best results! 🚀---⚠️ **Warning**: Render has 30-60s cold starts - may timeout with GUVI checker`}    Start-Sleep 30    curl https://your-app.onrender.com/healthwhile($true) { # 3. IMPORTANT: Keep warm before GUVI testing# Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT# Build Command: pip install -r requirements.txt# 2. Settings:# Go to render.com → New Web Service → Connect GitHub# 1. Connect to Render`powershellIf you must use free tier:## Alternative: Render (Free but Slower)---**Submit with confidence!** 🏆- 🚀 GUVI-ready (no timeouts)- ✅ Reliable (99.9% uptime)- ⚡ Fast (Railway optimized)**Your deployment is:**## 🎉 You're Done!---- [ ] URL + API key documented- [ ] Logs monitoring enabled- [ ] Warmup request sent- [ ] Speed test passed (<1s warm responses)- [ ] API endpoint tested (`/api/message`)- [ ] Health endpoint working (`/health`)- [ ] Environment variables set (ANTHROPIC_API_KEY, API_KEY)- [ ] Deployed to Railway successfullyBefore submitting to GUVI:## ✅ Final Checklist---`curl -H "x-api-key: guvi-secret-key-12345" https://your-app.up.railway.app/health# Check API key in request header`powershell### 403 Forbidden?`# Make sure ANTHROPIC_API_KEY is setrailway variables# Check if environment variables are set`powershell### Slow Responses?`railway up --forcerailway variables set PYTHON_VERSION=3.11# Common fixes:railway logs# Check logs`powershell### Deployment Failed?## 🆘 Troubleshooting---- Can cancel after event- More than enough for hackathon evaluation**Free Tier**: 500 hours/month ($5 credit)## 💰 Cost---- **No Timeouts**: ✅ Perfect for automated checker- **Uptime**: 99.9%- **Warm Response**: 200-500ms- **Cold Start**: 2-3 secondsRailway typically delivers:## ⚡ Performance Metrics---**Or in dashboard**: https://railway.app → Your Project → Logs`railway logs`powershell**View Logs:**## 📊 Monitor During Evaluation---`}  }    "locale": "IN"    "language": "English",    "channel": "SMS",  "metadata": {  "conversationHistory": [],  },    "timestamp": "2026-02-11T10:00:00Z"    "text": "Your account is blocked. Share OTP immediately.",    "sender": "scammer",  "message": {  "sessionId": "guvi-test-001",{`json**Sample Request:**`API Key: guvi-secret-key-12345  (in header: x-api-key)Method: POSTURL: https://your-app.up.railway.app/api/message`**Your Endpoint:**## 🎯 Submit to GUVI---``  }'    "metadata": {"channel": "SMS"}    "conversationHistory": [],    },      "timestamp": "2026-02-11T10:00:00Z"      "text": "Your account is blocked. Share OTP.",      "sender": "scammer",    "message": {    "sessionId": "warmup-001",  -d '{  -H "Content-Type: application/json" `  -H "x-api-key: guvi-secret-key-12345" `curl -X POST https://your-app.up.railway.app/api/message `# Send warmup request``powershell## Step 7: Warm Up Before GUVI Submission---- ✅ Grade: EXCELLENT- ✅ Warm response: 200-500ms- ✅ Cold start: 2-5 seconds**Expected Results:**`python test_deployment_speed.py# Test speed and reliability`powershell## Step 6: Test Your Deployment---`# https://your-app.up.railway.app# Your URL will be something like:railway domain# Generate public domain`powershell## Step 5: Get Your URL---**Or set in Railway dashboard**: Project Settings → Variables`railway variables set ANTHROPIC_MODEL=claude-haiku-4.5-20250110railway variables set LLM_PROVIDER=anthropicrailway variables set API_KEY=guvi-secret-key-12345railway variables set ANTHROPIC_API_KEY=your-anthropic-key-here# Required variables`powershellGo to Railway dashboard or use CLI:## Step 4: Set Environment Variables (1 minute)---- ✅ Assign a public URL- ✅ Build and deploy- ✅ Install dependencies- ✅ Detect Python appRailway will:`railway up# Deployrailway init# Initialize Railway projectcd "C:\Users\ASUS\Desktop\New folder\Work\AI Scammer Detection"# Navigate to your project`powershell## Step 3: Deploy Your App (2 minutes)---Creates a free Railway account (no credit card needed for 500 hours)`railway login# Open browser and login`powershell## Step 2: Login to Railway (1 minute)---**Don't have npm?** Download from: https://railway.app/cli```npm i -g @railway/cli# Install Railway CLI```powershell## Step 1: Install Railway CLI (1 minute)---**Why Railway?** Fastest response times + Best for GUVI checker + No cold starts## ⚡ **Quick Answer: Use Railway for Best Speed**

For GUVI hackathon, **Railway is the fastest and most reliable**:

- ⚡ **2-3s cold start** (vs Render's 30-60s)
- 🚀 **200-500ms warm responses**
- ✅ **No timeouts** for automated checker
- 💰 **$5/month** (cancel after hackathon)

---

## 📊 Speed Comparison

| Platform       | Cold Start | Warm Response | Free Tier  | GUVI Ready?   |
| -------------- | ---------- | ------------- | ---------- | ------------- |
| **Railway** ⭐ | 2-3s       | 200-500ms     | 500 hrs/mo | ✅ YES        |
| **Render**     | 30-60s ❌  | 300-800ms     | Forever    | ⚠️ Slow start |
| **Fly.io**     | 5-8s       | 400-700ms     | Limited    | ✅ YES        |
| **Vercel**     | N/A        | Timeouts ❌   | Yes        | ❌ NO         |

**Recommendation**: Use **Railway** for fast, reliable responses during GUVI evaluation.

---

## Production Deployment Checklist

### Pre-Deployment

- [x] All tests passing
- [x] Environment variables configured
- [x] Error handling validated
- [x] Rate limits understood
- [x] GUVI endpoint tested

## Deployment Options

### Option 1: Railway ⭐ (Recommended - Fastest)

**Why Railway?**

- ✅ Fastest cold starts (2-3s vs Render's 30-60s)
- ✅ Best for GUVI automated checker (no timeouts)
- ✅ Consistent performance (200-500ms warm responses)
- ✅ US-based servers (close to Anthropic/OpenAI APIs)
- 💰 $5/month (first 500 hours free)

**Quick Deploy (5 minutes):**

1. **Install Railway CLI**

   ```powershell
   npm i -g @railway/cli
   ```

2. **Login & Deploy**

   ```powershell
   railway login
   railway init
   railway up
   ```

3. **Set Environment Variables** (in Railway dashboard)

   ```
   ANTHROPIC_API_KEY=your-key-here
   API_KEY=guvi-secret-key-12345
   LLM_PROVIDER=anthropic
   ANTHROPIC_MODEL=claude-haiku-4.5-20250110
   ```

4. **Get Your URL**
   ```powershell
   railway domain (Free but Slow)
   ```

⚠️ **WARNING**: Render free tier has 30-60s cold starts - may timeout with GUVI checker!

**Only use if you must stay 100% free.**

1. **Create Render Account**
   - Go to render.com
   - Sign up with GitHub

2. **New Web Service**
   - Connect repository
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Environment Variables**

   ```
   ANTHROPIC_API_KEY=your-key
   API_KEY=guvi-secret-key-12345
   LLM_PROVIDER=anthropic
   ```

4. **Deploy**
   - Render builds automatically
   - Get URL: `https://your-app.onrender.com`

5. **Keep Warm Before GUVI Testing** ⚠️

   ```powershell
   # Run this 10 min before submission to prevent cold starts
   while($true) { curl https://your-app.onrender.com/health; Start-Sleep 30 }
   `` 0.0.0.0 --port $PORT`

   ```

6. **Environment Variables**

   ```
   GOOGLE_API_KEY=your-key
   API_KEY=honeypot-secret-2026
   ```

7. **Deploy**
   - Render builds automatically
   - Get URL: `https://your-app.onrender.com`

### Option 3: Ngrok (Local Testing)

1. **Install Ngrok**

   ```bash
   # Download from ngrok.com
   ngrok authtoken YOUR_TOKEN
   ```

2. **Start Server Locally**

   ```bash
   python main.py
   ```

3. **Expose via Ngrok**

   ```bash
   ngrok http 8000
   ```

4. **Get Public URL**
   - Copy the https URL: `https://abc123.ngrok.io`
   - ⚠️ **NOT recommended for GUVI** (unstable URL, changes on restart)

---

## 🎯 GUVI Checker Optimization

### Best Practices for GUVI Automated Testing

1. **Use Railway** (most reliable for automated checkers)
   - No cold starts after first request
   - Consistent response times
   - 99.9% uptime

2. **Test Before Submission**

   ```powershell
   # Test your deployment speed
   python test_deployment_speed.py
   ```

   **Expected Results:**
   - Cold start: < 5s ✅
   - Warm responses: < 1s ✅
   - API with LLM: 2-4s ✅

3. **Warm Up Your Endpoint Before GUVI Evaluation**

   ```powershell
   # Send a warmup request
   curl -X POST https://your-app.railway.app/api/message `
     -H "x-api-key: guvi-secret-key-12345" `
     -H "Content-Type: application/json" `
     -d '{"sessionId":"warmup","message":{"text":"test"}}'
   ```

4. **Monitor During Evaluation**
   - Railway Dashboard → Logs (real-time)
   - Watch for errors or rate limits
   - Check response times

---

## Post-Deployment Validation

### 1. Health Check

```bash
curl https://your-deployed-url.com/health
```

Expected:

```json
{
  "status": "healthy",
  "service": "AI Agentic Honeypot System",
  "version": "1.0.0"
}
```

### 2. Test Authentication

```bash
curl -X POST https://your-deployed-url.com/api/message \
  -H "x-api-key: wrong-key" \
  -d '{"session_id":"test","message":"test"}'
```

Expected: `403 Forbidden`

### 3. Test Scam Detection

```bash
curl -X POST https://your-deployed-url.com/api/message \
  -H "x-api-key: honeypot-secret-2026" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "deploy-test-001",
    "message": "Your account is blocked. Share OTP now."
  }'
```

Expected: `200 OK` with scam detected

### 4. Run Full Test Suite

```bash
# Update BASE_URL in test files
BASE_URL = "https://your-deployed-url.com"

# Run tests
cd tests
python test_guvi_endpoint.py
```

## GUVI Submission

### 1. Endpoint Information

```
URL: https://your-deployed-url.com/api/message
Method: POST
Authentication: Header x-api-key: honeypot-secret-2026
Content-Type: application/json
```

### 2. Request Format

```json
{
  "sessionId": "string",
  "message": {
    "sender": "scammer",
    "text": "string",
    "timestamp": "2026-01-27T12:00:00"
  },
  "conversationHistory": []
}
```

### 3. Response Format

```json
{
  "sessionId": "string",
  "isScam": true,
  "confidence": 0.95,
  "scamType": "bank_fraud",
  "reasoning": "string",
  "response": "string",
  "shouldContinue": true,
  "sessionComplete": false,
  "extractedIntelligence": {
    "phoneNumbers": [],
    "upiIds": [],
    "links": [],
    "keywords": []
  },
  "engagementMetrics": {
    "engagementDurationSeconds": 120,
    "totalMessagesExchanged": 5
  }
}
```

## Monitoring

### Check Logs

**Railway**: Dashboard → Logs
**Render**: Dashboard → Logs
**Local**: Console output

### Monitor Performance

```python
# Add to main.py if needed
import time

@app.middleware("http")
async def log_requests(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    print(f"Request took {duration:.2f}s")
    return response
```

## Troubleshooting

### Issue: 503 Service Unavailable

- **Cause**: Rate limits hit
- **Solution**: Wait 1 minute, system uses fallback

### Issue: Slow responses (>10s)

- **Cause**: LLM processing time
- **Solution**: Normal for complex requests, fallback kicks in

### Issue: 403 Forbidden

- **Cause**: Wrong/missing API key
- **Solution**: Check `x-api-key` header

### Issue: Environment variables not set

- **Cause**: Missing .env or platform config
- **Solution**: Add all required vars in platform dashboard

## Security Notes

1. **Never commit** `.env` file with real API keys
2. **Use environment variables** in production
3. **Rotate API keys** regularly
4. **Monitor usage** to detect abuse
5. **Rate limit** if needed (currently handled by Gemini)

## Performance Tips

1. **Enable Caching**: Already configured (100 items)
2. **Use Flash Models**: Already prioritized
3. **Monitor Quotas**: Gemini free tier limits
4. **Scale If Needed**: Railway/Render support auto-scaling

## Final Checklist Before Submission

- [ ] Server deployed and accessible
- [ ] Health endpoint returns 200
- [ ] Authentication working (403 for invalid key)
- [ ] Scam detection working (returns isScam=true for scams)
- [ ] AI responses generated
- [ ] Intelligence extracted correctly
- [ ] All GUVI tests passing
- [ ] Public URL documented
- [ ] API key shared with GUVI judges

## Support & Monitoring

### Set Up Alerts (Optional)

Use platforms like UptimeRobot to monitor:

- Endpoint availability
- Response times
- Error rates

### Log Analysis

Monitor for:

- High error rates
- Slow responses
- Authentication failures
- Rate limit hits

---

## 🎉 Deployment Complete!

Your AI Scammer Detection Honeypot is now production-ready!

---

## 📝 Quick Reference Card for GUVI

### **Best Platform: Railway ⭐**

- ✅ Fastest (200-500ms warm responses)
- ✅ No cold start issues for checker
- 💰 $5/month (first 500 hours free)

### **Deploy in 5 Minutes:**

```powershell
npm i -g @railway/cli
railway login
railway init
railway up
railway domain  # Get your URL
```

### **Set Environment Variables:**

```
ANTHROPIC_API_KEY=your-key-here
API_KEY=guvi-secret-key-12345
LLM_PROVIDER=anthropic
```

### **Test Performance:**

```powershell
python test_deployment_speed.py
# Expected: <500ms warm, <5s cold ✅
```

### **Before GUVI Submission Checklist:**

- [ ] Deployed to Railway
- [ ] Speed tested (<1s warm response)
- [ ] Warmup request sent
- [ ] Logs monitoring enabled
- [ ] URL + API key ready to submit

---

**Next Steps**:

1. ✅ Deploy to Railway (fastest, most reliable)
2. ✅ Test with `test_deployment_speed.py`
3. ✅ Warm up endpoint before submission
4. ✅ Submit URL to GUVI
5. ✅ Monitor logs during evaluation

**Good Luck! 🚀**
