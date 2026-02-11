# 🚀 Deployment Guide - AI Scammer Detection Honeypot

## Production Deployment Checklist

### Pre-Deployment

- [x] All tests passing
- [x] Environment variables configured
- [x] Error handling validated
- [x] Rate limits understood
- [x] GUVI endpoint tested

## Deployment Options

### Option 1: Railway (Recommended)

1. **Create Railway Account**
   - Go to railway.app
   - Sign up with GitHub

2. **Deploy from GitHub**

   ```bash
   # Push your code to GitHub
   git init
   git add .
   git commit -m "Production ready"
   git push origin main
   ```

3. **Connect to Railway**
   - New Project → Deploy from GitHub
   - Select your repository
   - Railway auto-detects Python

4. **Set Environment Variables**

   ```
   GOOGLE_API_KEY=your-key-here
   API_KEY=honeypot-secret-2026
   PORT=8000
   ```

5. **Deploy**
   - Railway automatically builds and deploys
   - Get your public URL: `https://your-app.railway.app`

### Option 2: Render

1. **Create Render Account**
   - Go to render.com
   - Sign up with GitHub

2. **New Web Service**
   - Connect repository
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Environment Variables**

   ```
   GOOGLE_API_KEY=your-key
   API_KEY=honeypot-secret-2026
   ```

4. **Deploy**
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

Your AI Scammer Detection Honeypot is now production-ready and deployed!

**Next Steps**:

1. Submit URL to GUVI
2. Share API key with judges
3. Monitor during evaluation
4. Be ready for demo

**Good Luck! 🚀**
