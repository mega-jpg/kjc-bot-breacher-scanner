from fastapi import APIRouter, HTTPException
from typing import Dict
from botnet_service import get_botnet_service
from urllib.parse import unquote

router = APIRouter()



# ==== DORK HARVESTER BACKEND ====
import threading
import requests
import random
import time
from queue import Queue
from bs4 import BeautifulSoup

# Global state for harvester
harvester_state = {
    "status": "idle",  # idle, running, completed
    "shops_found": 0,
    "active_threads": 0,
    "current_engine": "",
    "recent_shops": [],
    "seen": set(),
    "stop_flag": False,
    "config": {}
}

# Function to load dorks from file dynamically
def load_dorks_from_file(filename="dorks_template.txt"):
    """Load dorks from external file at runtime"""
    import os
    dorks = []
    
    if not os.path.exists(filename):
        print(f"[WARNING] {filename} not found, using fallback dorks")
        return [
            'site:myshopify.com',
            'inurl:shopify.com/products',
            'inurl:myshopify.com/collections',
            'inurl:wc/v3/products "WooCommerce"',
            'inurl:opencart "index.php?route=product"'
        ]
    
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    dorks.append(line)
        
        print(f"[✓] Loaded {len(dorks)} dorks from {filename}")
        return dorks
    except Exception as e:
        print(f"[ERROR] Failed to load dorks from {filename}: {str(e)}")
        return []

# Load dorks dynamically at module initialization
DORKS = load_dorks_from_file("dorks_template.txt")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/129.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/129.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
]

def get_ua():
    return random.choice(USER_AGENTS)

def get_proxy():
    try:
        response = requests.get("https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5", timeout=8)
        proxies = response.text.splitlines()
        if proxies:
            return random.choice(proxies)
    except:
        pass
    return None

def harvest_dork(dork, config):
    """Harvest one dork across multiple engines with auto-stop when exhausted"""
    global harvester_state
    
    if harvester_state["stop_flag"]:
        return
    
    headers = {"User-Agent": get_ua() if config.get("use_ua_rotation") else USER_AGENTS[0]}
    
    engines_to_use = []
    if config["engines"].get("duckduckgo"):
        engines_to_use.append("duckduckgo")
    if config["engines"].get("google"):
        engines_to_use.append("google")
    if config["engines"].get("bing"):
        engines_to_use.append("bing")
    if config["engines"].get("yandex"):
        engines_to_use.append("yandex")
    
    for engine in engines_to_use:
        if harvester_state["stop_flag"]:
            break
            
        harvester_state["current_engine"] = engine
        
        # Auto-stop logic
        max_empty_pages = 3  # Stop after 3 consecutive pages with no new shops
        empty_page_count = 0
        max_pages = 100  # Hard limit to prevent infinite loops
        
        for page_num in range(max_pages):
            page = page_num * 10  # Convert to offset (0, 10, 20, ...)
            
            if harvester_state["stop_flag"]:
                break
                
            urls = {
                "duckduckgo": f"https://html.duckduckgo.com/html/?q={requests.utils.quote(dork)}",
                "google": f"https://www.google.com/search?q={requests.utils.quote(dork)}&start={page}",
                "bing": f"https://www.bing.com/search?q={requests.utils.quote(dork)}&first={page+1}",
                "yandex": f"https://yandex.com/search/?text={requests.utils.quote(dork)}&p={page_num}"
            }
            
            try:
                # Retry logic for connection timeouts
                max_retries = 3
                retry_delay = 5
                html_content = None
                
                for retry in range(max_retries):
                    try:
                        proxy_dict = None
                        if config.get("use_proxies"):
                            proxy = get_proxy()
                            if proxy:
                                proxy_dict = {"https": f"socks5://{proxy}"}
                        
                        # DuckDuckGo requires form POST for search
                        if engine == "duckduckgo":
                            r = requests.post("https://html.duckduckgo.com/html/", 
                                             data={"q": dork, "s": str(page)},
                                             headers=headers, 
                                             proxies=proxy_dict, 
                                             timeout=30)  # Increased from 10 to 30
                        else:
                            r = requests.get(urls[engine], headers=headers, proxies=proxy_dict, timeout=30)
                        
                        html_content = r.text
                        break  # Success, exit retry loop
                        
                    except requests.exceptions.Timeout:
                        if retry < max_retries - 1:
                            print(f"[WARNING] {engine} page {page_num}: Timeout (attempt {retry+1}/{max_retries}), retrying in {retry_delay}s...")
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                        else:
                            print(f"[ERROR] {engine} page {page_num}: Max retries exceeded, skipping page")
                            raise  # Re-raise to trigger outer exception handler
                
                if html_content is None:
                    continue  # Skip this page if all retries failed
                
                # DEBUG: Save HTML response to file for inspection
                debug_file = f"debug_{engine}_page{page_num}.html"
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(html_content)
                print(f"[DEBUG] {engine} page {page_num}: Length {len(html_content)} bytes, Saved to {debug_file}")
                
                # CAPTCHA detection (Cloudflare, Yandex SmartCaptcha, Google reCAPTCHA, etc.)
                response_lower = html_content.lower()
                captcha_detected = False
                captcha_type = ""
                
                if "cloudflare" in response_lower and "turnstile" in response_lower:
                    captcha_detected = True
                    captcha_type = "Cloudflare Turnstile"
                elif "smartcaptcha" in response_lower or "are you not a robot" in response_lower:
                    captcha_detected = True
                    captcha_type = "Yandex SmartCaptcha"
                elif "recaptcha" in response_lower or "g-recaptcha" in response_lower:
                    captcha_detected = True
                    captcha_type = "Google reCAPTCHA"
                elif "captcha" in response_lower and len(html_content) < 50000:
                    captcha_detected = True
                    captcha_type = "Unknown CAPTCHA"
                
                if captcha_detected:
                    print(f"[ERROR] {engine} blocked by {captcha_type}")
                    print(f"[ERROR] Cannot bypass CAPTCHA - switching to DuckDuckGo recommended")
                    break  # Exit pagination loop for this engine
                
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract URLs based on engine
                found_links = []
                
                if engine == "duckduckgo":
                    # DuckDuckGo HTML: <a class="result__a" href="https://...">
                    for a in soup.find_all('a', class_='result__a'):
                        href = a.get('href', '')
                        if href.startswith('http'):
                            found_links.append(unquote(href))
                    
                    # Also try snippet links
                    for a in soup.find_all('a', class_='result__snippet'):
                        href = a.get('href', '')
                        if href.startswith('http'):
                            found_links.append(unquote(href))
                
                elif engine == "google":
                    # Google: <a href="/url?q=https://..." or <a href="https://...">
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        # Google redirects: /url?q=ACTUAL_URL
                        if '/url?q=' in href:
                            actual_url = href.split('/url?q=')[1].split('&')[0]
                            if actual_url.startswith('http'):
                                found_links.append(unquote(actual_url))
                        # Direct links
                        elif href.startswith('http') and not any(x in href for x in ['google.com', 'gstatic.com', 'googleapis.com']):
                            found_links.append(unquote(href))
                
                elif engine == "bing":
                    # Bing: parse results properly
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if href.startswith('http') and not any(x in href for x in ['bing.com', 'microsoft.com', 'msn.com']):
                            found_links.append(unquote(href))
                
                elif engine == "yandex":
                    # Yandex: parse results
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if href.startswith('http') and 'yandex' not in href:
                            found_links.append(unquote(href))
                
                print(f"[DEBUG] {engine} page {page_num}: Extracted {len(found_links)} raw links")
                
                # Track new unique shops found on this page
                new_shops_found = 0
                
                # Process found links
                for link in found_links:
                    # Clean URL
                    try:
                        shop = unquote(link.split('?')[0])  # Remove query params
                        
                        # Filter valid shop URLs
                        if shop.startswith('http') and len(shop) > 15:
                            # Skip common non-shop domains
                            skip_domains = ['facebook.com', 'twitter.com', 'youtube.com', 'linkedin.com', 
                                          'instagram.com', 'github.com', 'wordpress.org', 'w3.org', 
                                          'wikipedia.org']
                            
                            is_blocked = any(domain in shop.lower() for domain in skip_domains)
                            
                            if not is_blocked:
                                if shop not in harvester_state["seen"]:
                                    harvester_state["seen"].add(shop)
                                    harvester_state["shops_found"] += 1
                                    harvester_state["recent_shops"].insert(0, shop)
                                    new_shops_found += 1
                                    
                                    # Keep only last 50 recent shops
                                    if len(harvester_state["recent_shops"]) > 50:
                                        harvester_state["recent_shops"] = harvester_state["recent_shops"][:50]
                                    
                                    # Save to file
                                    with open("shops_fresh_2025.txt", "a", encoding="utf-8") as f:
                                        f.write(shop + "\n")
                                    
                                    print(f"[+] Shop found: {shop}")
                    except:
                        continue
                
                # Auto-stop logic: check if we found any NEW shops
                if new_shops_found == 0:
                    empty_page_count += 1
                    print(f"[{engine}] Page {page_num}: No new shops found ({empty_page_count}/{max_empty_pages})")
                    
                    if empty_page_count >= max_empty_pages:
                        print(f"[✓] {engine}: Exhausted all unique shops for dork (stopped at page {page_num})")
                        break  # Move to next engine or dork
                else:
                    empty_page_count = 0  # Reset counter when we find new shops
                    print(f"[{engine}] Page {page_num}: Found {new_shops_found} new unique shops")
                        
            except Exception as e:
                print(f"[ERROR] {engine} page {page_num}: {str(e)}")
                continue
            
            # Delay to avoid blocking
            time.sleep(random.uniform(1, 3))
    
    harvester_state["active_threads"] -= 1

@router.post("/dork-harvest/start")
async def start_dork_harvest(request: Dict):
    """Start dork harvesting with multi-threading"""
    global harvester_state
    
    if harvester_state["status"] == "running":
        return {
            "status": "error",
            "message": "Harvester is already running"
        }
    
    # Handle clear/append mode based on user choice
    import os
    output_file = "shops_fresh_2025.txt"
    existing_shops = set()
    clear_results = request.get("clear_results", True)  # Default: clear mode
    
    if clear_results:
        # Clear mode: delete old file
        if os.path.exists(output_file):
            os.remove(output_file)
            print(f"[✓] Cleared previous results from {output_file}")
    else:
        # Append mode: load existing shops to avoid duplicates
        if os.path.exists(output_file):
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    for line in f:
                        shop = line.strip()
                        if shop:
                            existing_shops.add(shop)
                print(f"[✓] Loaded {len(existing_shops)} existing shops from {output_file} (append mode)")
            except Exception as e:
                print(f"[WARNING] Could not load existing shops: {str(e)}")
    
    # Reset state
    harvester_state = {
        "status": "running",
        "shops_found": 0,
        "active_threads": 0,
        "current_engine": "",
        "recent_shops": [],
        "seen": existing_shops,  # Empty set in clear mode, pre-loaded in append mode
        "stop_flag": False,
        "config": request
    }
    
    # Get dorks to use
    dork_count = min(request.get("dork_count", 50), len(DORKS))
    dorks_to_use = DORKS[:dork_count]
    thread_count = request.get("thread_count", 10)
    
    # Start threads
    def run_harvester():
        threads = []
        for dork in dorks_to_use:
            if harvester_state["stop_flag"]:
                break
            
            harvester_state["active_threads"] += 1
            t = threading.Thread(target=harvest_dork, args=(dork, request))
            t.daemon = True
            t.start()
            threads.append(t)
            
            # Limit concurrent threads
            if len([t for t in threads if t.is_alive()]) >= thread_count:
                time.sleep(5)
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        harvester_state["status"] = "completed"
        harvester_state["active_threads"] = 0
    
    # Run in background
    bg_thread = threading.Thread(target=run_harvester)
    bg_thread.daemon = True
    bg_thread.start()
    
    return {
        "status": "success",
        "message": f"Dork harvester started with {dork_count} dorks and {thread_count} threads"
    }

@router.post("/dork-harvest/stop")
async def stop_dork_harvest():
    """Stop dork harvesting"""
    global harvester_state
    
    harvester_state["stop_flag"] = True
    harvester_state["status"] = "idle"
    
    return {
        "status": "success",
        "message": "Harvester stopped",
        "total_shops": harvester_state["shops_found"]
    }

@router.get("/dork-harvest/status")
async def get_dork_harvest_status():
    """Get current status of dork harvester"""
    return {
        "status": harvester_state["status"],
        "shops_found": harvester_state["shops_found"],
        "active_threads": harvester_state["active_threads"],
        "current_engine": harvester_state["current_engine"],
        "recent_shops": harvester_state["recent_shops"][:10]  # Last 10 shops
    }
