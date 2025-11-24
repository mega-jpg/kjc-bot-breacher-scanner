# 🔥 FlareSolverr Setup Guide

## What is FlareSolverr?

**FlareSolverr** is a proxy server that bypasses Cloudflare and other anti-bot protections. It uses Selenium WebDriver with undetected-chromedriver to solve CAPTCHA challenges automatically.

### Features:
- ✅ Bypass Cloudflare Turnstile
- ✅ Bypass Google reCAPTCHA
- ✅ Bypass Yandex SmartCaptcha
- ✅ HTTP API (no Selenium code needed in your app)
- ✅ Automatic CAPTCHA solving
- ✅ Session management

---

## 🐳 Quick Start with Docker (Recommended)

### 1. Install Docker Desktop
Download: https://www.docker.com/products/docker-desktop/

### 2. Run FlareSolverr Container
```bash
docker run -d \
  --name=flaresolverr \
  -p 8191:8191 \
  -e LOG_LEVEL=info \
  --restart unless-stopped \
  ghcr.io/flaresolverr/flaresolverr:latest
```

**Windows PowerShell:**
```powershell
docker run -d --name=flaresolverr -p 8191:8191 -e LOG_LEVEL=info --restart unless-stopped ghcr.io/flaresolverr/flaresolverr:latest
```

### 3. Verify FlareSolverr is Running
Open browser: http://localhost:8191

You should see:
```json
{
  "msg": "FlareSolverr is ready!",
  "version": "v3.x.x",
  "userAgent": "Mozilla/5.0..."
}
```

---

## ⚙️ Enable FlareSolverr in Bot

### Option 1: Environment Variables (Recommended)

Create `.env` file in project root:
```env
USE_FLARESOLVERR=true
FLARESOLVERR_URL=http://localhost:8191/v1
```

### Option 2: Modify Code Directly

Edit `botnet_routes.py`:
```python
# Change this line:
USE_FLARESOLVERR = os.getenv("USE_FLARESOLVERR", "false").lower() == "true"

# To:
USE_FLARESOLVERR = True
```

---

## 🚀 How to Use

### 1. Start FlareSolverr
```bash
docker start flaresolverr
```

### 2. Enable in Bot
Set `USE_FLARESOLVERR=true` in `.env`

### 3. Run Harvester
```bash
python main.py
```

### 4. Test with Google/Bing/Yandex
- Check **Google** engine in UI
- Click **Start Harvesting**
- Watch console logs for `[FlareSolverr] ✓ Bypassed CAPTCHA`

---

## 📊 Performance Expectations

| Engine | Without FlareSolverr | With FlareSolverr |
|--------|---------------------|-------------------|
| DuckDuckGo | ✅ Fast (2-5s/page) | Not needed |
| Google | ❌ reCAPTCHA blocked | ✅ Slow (15-30s/page) |
| Bing | ❌ Cloudflare blocked | ✅ Slow (15-30s/page) |
| Yandex | ❌ SmartCaptcha blocked | ✅ Slow (15-30s/page) |

**Note:** FlareSolverr is **10x slower** than direct requests because it needs to:
1. Launch headless Chrome
2. Wait for page load
3. Solve CAPTCHA challenge
4. Extract HTML

**Recommendation:** Use **DuckDuckGo** for fast harvesting, enable FlareSolverr **only** when you need Google/Bing/Yandex specifically.

---

## 🔧 Advanced Configuration

### Increase Timeout (for slow CAPTCHAs)
```python
# In botnet_routes.py, find:
def flaresolverr_request(url, max_timeout=60000):

# Change to:
def flaresolverr_request(url, max_timeout=120000):  # 2 minutes
```

### Use FlareSolverr with Proxies
```bash
docker run -d \
  --name=flaresolverr \
  -p 8191:8191 \
  -e LOG_LEVEL=info \
  -e PROXY_SERVER=http://your-proxy:port \
  --restart unless-stopped \
  ghcr.io/flaresolverr/flaresolverr:latest
```

### Check FlareSolverr Logs
```bash
docker logs -f flaresolverr
```

---

## 🐛 Troubleshooting

### FlareSolverr not responding
```bash
# Restart container
docker restart flaresolverr

# Check logs
docker logs flaresolverr
```

### "Connection refused" error
- Make sure Docker is running
- Verify port 8191 is not blocked by firewall
- Check http://localhost:8191 in browser

### Still getting CAPTCHA after using FlareSolverr
- Increase `max_timeout` to 120000 (2 minutes)
- Check FlareSolverr logs for errors
- Try restarting FlareSolverr container
- Some CAPTCHAs are too hard even for FlareSolverr

### Chrome/ChromeDriver errors in logs
```bash
# Update FlareSolverr to latest version
docker pull ghcr.io/flaresolverr/flaresolverr:latest
docker stop flaresolverr
docker rm flaresolverr
# Run the docker run command again
```

---

## 🎯 Usage Recommendations

### For Maximum Speed:
✅ **DuckDuckGo only** (no FlareSolverr needed)
- 200 dorks × 10 threads = ~2,000 shops in 15 minutes

### For Maximum Coverage:
✅ **DuckDuckGo + Google (with FlareSolverr)**
- 100 dorks DDG (fast) + 20 dorks Google (slow)
- ~1,500 shops in 30 minutes

### NOT Recommended:
❌ All 4 engines with FlareSolverr
- Too slow (3+ hours for 200 dorks)
- High RAM usage (4GB+ for Chrome instances)

---

## 📝 Example Usage

### Scenario: Harvest 1000+ shops fast

**Config:**
```
Engines: ✅ DuckDuckGo only
Dorks: 150
Threads: 20
FlareSolverr: ❌ Disabled
```

**Result:** ~1,500 unique shops in 20 minutes

---

### Scenario: Need Google-specific results

**Config:**
```
Engines: ✅ Google only
Dorks: 30
Threads: 3 (FlareSolverr can't handle many parallel)
FlareSolverr: ✅ Enabled
```

**Result:** ~300 unique shops in 45 minutes

---

## 🔗 Resources

- FlareSolverr GitHub: https://github.com/FlareSolverr/FlareSolverr
- Docker Hub: https://hub.docker.com/r/flaresolverr/flaresolverr
- API Documentation: https://github.com/FlareSolverr/FlareSolverr#api

---

## ⚠️ Legal Disclaimer

FlareSolverr bypasses anti-bot protections. Use responsibly and only on websites you have permission to scrape. Respect robots.txt and rate limits.
