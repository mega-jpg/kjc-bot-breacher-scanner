# 🔍 Dork Harvester 2025 - Documentation

## Overview
Multi-engine shop scanner with proxy rotation & real-time harvesting capabilities.

## Features
✅ **Multi-Engine Support**
- Google Search
- Bing Search  
- Yandex Search

✅ **Advanced Protection**
- SOCKS5 Proxy Rotation (922S5 + public proxies)
- User-Agent Rotation (5000+ real UAs)
- Random delay between requests (2-6 seconds)
- Multi-threading support (1-50 threads)

✅ **200 Dorks Database**
- Magento (30 dorks)
- WooCommerce (40 dorks)
- OpenCart (30 dorks)
- PrestaShop (25 dorks)
- Shopify (20 dorks)
- Other platforms (55 dorks)

✅ **Real-time Monitoring**
- Live shop counter
- Active threads tracking
- Current engine indicator
- Runtime timer
- Recent shops log

## Usage

### 1. Start the Server
```bash
python main.py
```

### 2. Access Web Interface
Open browser: `http://localhost:8000`

### 3. Configure Harvester
- Select search engines (Google/Bing/Yandex)
- Set number of dorks (1-200)
- Set thread count (1-50 for VPS mode)
- Set pages per engine (1-100)
- Enable/disable proxy rotation
- Enable/disable UA rotation

### 4. Start Harvesting
Click **"🚀 Start Harvesting"** button

### 5. Monitor Progress
Watch live statistics:
- Shops found counter
- Active threads
- Current engine
- Runtime
- Recent shops (scrollable log)

### 6. Stop Harvester
Click **"⛔ Stop Harvester"** button anytime

## API Endpoints

### POST /api/dork-harvest/start
Start dork harvesting
```json
{
  "engines": {
    "google": true,
    "bing": true,
    "yandex": false
  },
  "dork_count": 50,
  "thread_count": 10,
  "pages_limit": 50,
  "use_proxies": true,
  "use_ua_rotation": true
}
```

### POST /api/dork-harvest/stop
Stop dork harvesting
```json
{
  "status": "success",
  "total_shops": 1234
}
```

### GET /api/dork-harvest/status
Get current status
```json
{
  "status": "running",
  "shops_found": 123,
  "active_threads": 8,
  "current_engine": "google",
  "recent_shops": ["https://shop1.com", "https://shop2.com"]
}
```

## Output

Results are saved to: `shops_fresh_2025.txt`

Format:
```
https://example-shop1.com/magento/
https://example-shop2.com/woocommerce/
https://example-shop3.com/opencart/
```

## Performance Tips

### VPS Mode (Recommended)
- Use 10-20 threads
- Enable proxy rotation
- Use all 3 engines
- Set 50-100 dorks

### Local Mode
- Use 3-5 threads
- Disable proxies (faster locally)
- Use 1-2 engines
- Set 10-20 dorks

### Maximum Performance (10 VPS)
- Run 10 instances on different VPS
- Each VPS: 10 threads
- Total: 100 parallel threads
- Expected: 10,000-50,000 shops/day

## Troubleshooting

### No shops found
- Try different engines
- Reduce thread count
- Enable proxy rotation
- Check internet connection

### Too many errors
- Reduce thread count
- Increase delay between requests
- Use fewer dorks
- Try different proxies

### Slow harvesting
- Increase thread count
- Disable proxies (if local)
- Use fewer engines
- Reduce pages per engine

## Legal Notice
⚠️ **For Educational & Testing Purposes Only**

This tool is designed for:
- Security research
- Penetration testing
- E-commerce platform analysis
- Academic purposes

**NOT for:**
- Illegal activities
- DDOS attacks
- Unauthorized access
- Data theft

Always respect robots.txt and website terms of service.

## Credits
- KJC Group Development Team
- Built with FastAPI + BeautifulSoup4
- Proxy API: ProxyScrape
