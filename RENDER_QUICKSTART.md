# 🎯 Render Deployment - Quick Start Guide (With Cron Jobs)

**100% FREE deployment with NO cold starts!**

---

## ⚡ What You Get

✅ **Free hosting** on Render  
✅ **Automatic keep-alive** via cron job  
✅ **Fast responses** (300-800ms, no 30-60s delays)  
✅ **Perfect for GUVI checker** (no timeouts)

---

## 🚀 Deploy in 10 Minutes

### Step 1: Push to GitHub (if not done)

```powershell
git add .
git commit -m "Add Render deployment with cron jobs"
git push origin main
```

### Step 2: Create Web Service on Render

1. Go to **https://render.com** and sign up (free)
2. Click **"New +"** → **"Web Service"**
3. Connect GitHub → Select your repo
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add **Environment Variables**:
   ```
   ANTHROPIC_API_KEY=your-key-here
   API_KEY=guvi-secret-key-12345
   LLM_PROVIDER=anthropic
   ```
6. Click **"Create Web Service"**
7. **Copy your URL**: `https://your-app-name.onrender.com`

### Step 3: Create Cron Job (Keep-Alive)

1. Click **"New +"** → **"Cron Job"**
2. Select same GitHub repo
3. Configure:
   - **Build Command**: `pip install requests`
   - **Command**: `python scripts/keep_alive.py`
   - **Schedule**: `*/10 * * * *`
4. Add **Environment Variable**:
   ```
   RENDER_EXTERNAL_URL=https://your-app-name.onrender.com
   ```
   (Use YOUR actual URL from Step 2!)
5. Click **"Create Cron Job"**

### Step 4: Verify Everything Works

```powershell
# Test once deployed
curl https://your-app-name.onrender.com/health

# Should return 200 OK immediately (no 30s wait)
```

---

## ✅ That's It!

Your app now:

- ✅ Stays awake 24/7 (cron pings every 10 min)
- ✅ Responds fast (no cold starts)
- ✅ Costs $0 (completely free)
- ✅ Ready for GUVI evaluation

---

## 📊 How It Works

```
╔═══════════════════════╗
║   Your Render App     ║  ← Main web service
╚═══════════════════════╝
          ↑
          │ Ping /health
          │ Every 10 minutes
          │
╔═══════════════════════╗
║   Cron Job Service    ║  ← Keep-alive worker
╚═══════════════════════╝
```

**Result**: App never sleeps, always responds fast! 🚀

---

## 🎯 Submit to GUVI

**Your API Endpoint:**

```
URL: https://your-app-name.onrender.com/api/message
Method: POST
Header: x-api-key: guvi-secret-key-12345
```

**Test it:**

```powershell
curl -X POST https://your-app-name.onrender.com/api/message `
  -H "x-api-key: guvi-secret-key-12345" `
  -H "Content-Type: application/json" `
  -d '{
    "sessionId":"test",
    "message":{
      "text":"Your account is blocked. Share OTP.",
      "sender":"scammer"
    }
  }'
```

---

## 🔧 Troubleshooting

### Still seeing cold starts?

**Check cron job is running:**

1. Render → Your Cron Job → Logs
2. Should see entries every 10 minutes
3. Should show "✅ Service is alive!"

### Cron job failing?

**Common issues:**

- ❌ `RENDER_EXTERNAL_URL` not set → Add it!
- ❌ Wrong URL format → Should include `https://`
- ❌ Wrong schedule → Use `*/10 * * * *`

### Need more reliability?

**Option 1: Increase cron frequency**

```
*/5 * * * *   # Every 5 minutes instead of 10
```

**Option 2: Add UptimeRobot (free)**

- Go to uptimerobot.com
- Add monitor for your `/health` endpoint
- Check every 5 minutes
- Now you have 2 services keeping it warm! 🔥

---

## 📁 Files Created

✅ [render.yaml](render.yaml) - Deployment configuration  
✅ [scripts/keep_alive.py](scripts/keep_alive.py) - Cron job script  
✅ [RENDER_CRONJOB_GUIDE.md](RENDER_CRONJOB_GUIDE.md) - Detailed guide  
✅ [keep_alive_local.ps1](keep_alive_local.ps1) - Local Windows script (backup)

---

## 💡 Pro Tips

1. **Deploy 24h before GUVI evaluation** - Ensure everything works
2. **Check logs regularly** - Monitor cron job execution
3. **Test response times** - Use `test_deployment_speed.py`
4. **Keep cron running during eval** - Don't delete it!

---

## 🆚 Why Cron Jobs vs Paid Railway?

| Feature       | Render + Cron (FREE) | Railway ($5) |
| ------------- | -------------------- | ------------ |
| Cost          | $0                   | $5/month     |
| Cold Start    | ~2-5s (with cron)    | 0s           |
| Warm Response | 300-800ms            | 200-500ms    |
| GUVI Ready    | ✅ YES               | ✅ YES       |
| Setup Time    | 10 min               | 5 min        |

**Verdict**: Both work great! Use Render+Cron if you want FREE. ✨

---

**🎉 You're all set! Deploy with confidence.**

For detailed troubleshooting, see: [RENDER_CRONJOB_GUIDE.md](RENDER_CRONJOB_GUIDE.md)
