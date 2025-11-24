from fastapi import APIRouter, HTTPException
from typing import Dict
from botnet_service import get_botnet_service
from urllib.parse import unquote
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

router = APIRouter()



# ==== DORK HARVESTER BACKEND ====
import threading
import requests
import random
import time
from queue import Queue
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime

@router.get("/ghdb/info")
async def get_ghdb_info():
    """Get GHDB database information (last updated timestamp)"""
    ghdb_file = "module/pagodo/dorks/all_google_dorks.txt"
    
    if not os.path.exists(ghdb_file):
        return {
            "exists": False,
            "message": "GHDB database not found. Run: python -m module.pagodo.ghdb_scraper"
        }
    
    file_stat = os.stat(ghdb_file)
    modified_time = datetime.fromtimestamp(file_stat.st_mtime)
    age_seconds = (datetime.now() - modified_time).total_seconds()
    age_days = int(age_seconds / 86400)
    age_hours = int((age_seconds % 86400) / 3600)
    
    # Count dorks
    try:
        with open(ghdb_file, 'r', encoding='utf-8') as f:
            dork_count = sum(1 for line in f if line.strip())
    except:
        dork_count = 0
    
    return {
        "exists": True,
        "last_updated": modified_time.strftime("%Y-%m-%d %H:%M:%S"),
        "age_days": age_days,
        "age_hours": age_hours,
        "dork_count": dork_count,
        "cli_command": "python -m module.pagodo.ghdb_scraper"
    }

# Global state for harvester
harvester_state = {
    "status": "idle",  # idle, running, completed
    "shops_found": 0,
    "active_threads": 0,
    "current_engine": "",
    "recent_shops": [],
    "stop_flag": False,
    "config": {},
    "proxy_rotation_index": 0,  # Pagodo-style round-robin proxy rotation
    "delay_list": []  # Pagodo-style intelligent delay list
}

# GHDB Categories (from Pagodo)
GHDB_CATEGORIES = {
    "all": "all_google_dorks.txt",
    "footholds": "footholds.dorks",
    "usernames": "files_containing_usernames.dorks",
    "sensitive_directories": "sensitive_directories.dorks",
    "web_server_detection": "web_server_detection.dorks",
    "vulnerable_files": "vulnerable_files.dorks",
    "vulnerable_servers": "vulnerable_servers.dorks",
    "error_messages": "error_messages.dorks",
    "juicy_info": "files_containing_juicy_info.dorks",
    "passwords": "files_containing_passwords.dorks",
    "shopping_info": "sensitive_online_shopping_info.dorks",
    "network_data": "network_or_vulnerability_data.dorks",
    "login_portals": "pages_containing_login_portals.dorks",
    "online_devices": "various_online_devices.dorks",
    "advisories": "advisories_and_vulnerabilities.dorks"
}

# Function to load Shodan dorks (different syntax)
def load_shodan_dorks(filename="inputDork/shodan_dorks.txt"):
    """Load Shodan-specific queries (different from Google dorks)"""
    import os
    queries = []
    
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        queries.append(line)
            print(f"[✓] Loaded {len(queries)} Shodan queries from {filename}")
            return queries
        except Exception as e:
            print(f"[ERROR] Failed to load Shodan dorks: {str(e)}")
    else:
        print(f"[WARNING] Shodan dorks file not found: {filename}")
    
    return []

# Function to load dorks from file dynamically
def load_dorks_from_file(filename="inputDork/general_search_dorks.txt", use_ghdb=False, ghdb_category="all"):
    """Load dorks from external file or GHDB database
    
    Args:
        filename: Custom dork file path
        use_ghdb: If True, load from Pagodo GHDB dorks
        ghdb_category: GHDB category to load (all, vulnerable_files, login_portals, etc.)
    """
    import os
    dorks = []
    
    # Load from GHDB if requested
    if use_ghdb:
        ghdb_file = GHDB_CATEGORIES.get(ghdb_category, "all_google_dorks.txt")
        ghdb_path = f"module/pagodo/dorks/{ghdb_file}"
        
        if os.path.exists(ghdb_path):
            try:
                with open(ghdb_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            dorks.append(line)
                print(f"[✓] Loaded {len(dorks)} GHDB dorks from category: {ghdb_category}")
                return dorks
            except Exception as e:
                print(f"[ERROR] Failed to load GHDB dorks: {str(e)}")
        else:
            print(f"[WARNING] GHDB file not found: {ghdb_path}")
    
    # Fallback to custom file
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

# Load dorks dynamically at module initialization (custom dorks by default)
DORKS = load_dorks_from_file("inputDork/general_search_dorks.txt", use_ghdb=False)

# ==== SQLite Database Helper Functions ====
DB_PATH = "harvested_shops.db"

def init_database():
    """Initialize SQLite database and create tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create shops table with unique constraint on domain
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT UNIQUE NOT NULL,
            engine TEXT NOT NULL,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create index for fast lookup
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_domain ON shops(domain)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_engine ON shops(engine)')
    
    conn.commit()
    conn.close()
    print(f"[✓] Database initialized: {DB_PATH}")

def check_and_insert_shop(domain, engine):
    """Check if shop exists, insert if new. Returns True if inserted (new shop)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Try to insert (will fail if duplicate due to UNIQUE constraint)
        cursor.execute(
            "INSERT INTO shops (domain, engine, discovered_at) VALUES (?, ?, ?)",
            (domain, engine, datetime.now())
        )
        conn.commit()
        conn.close()
        return True  # New shop inserted
    except sqlite3.IntegrityError:
        # Duplicate found
        conn.close()
        return False

def get_shop_count_by_engine(engine):
    """Get total shops count for specific engine"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM shops WHERE engine = ?", (engine,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def export_shops_to_file(engine, output_file):
    """Export shops from database to text file"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT domain FROM shops WHERE engine = ? ORDER BY discovered_at DESC", (engine,))
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for row in cursor.fetchall():
            f.write(row[0] + '\n')
    
    conn.close()
    print(f"[✓] Exported {engine} shops to {output_file}")

def clear_shops_by_engine(engine):
    """Delete all shops for specific engine from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shops WHERE engine = ?", (engine,))
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"[✓] Cleared {deleted_count} shops from {engine} in database")
    return deleted_count

# Initialize database on module load
init_database()

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
    """Legacy random proxy selection (API-based)"""
    try:
        response = requests.get("https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5", timeout=8)
        proxies = response.text.splitlines()
        if proxies:
            return random.choice(proxies)
    except:
        pass
    return None

# Shodan API search (requires API key)
def search_shodan(query, api_key=None, page=1):
    """Search Shodan API with query
    
    Args:
        query: Shodan query string (e.g., 'product:Magento country:VN')
        api_key: Shodan API key (get from SHODAN_API_KEY env var)
        page: Results page number
    
    Returns:
        list: IP addresses and basic info
    """
    if not api_key:
        api_key = os.getenv("SHODAN_API_KEY")
        if not api_key:
            print("[ERROR] SHODAN_API_KEY not found in environment variables")
            return []
    
    try:
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.shodan.io/shodan/host/search?key={api_key}&query={encoded_query}&page={page}"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            for match in data.get('matches', []):
                ip = match.get('ip_str')
                port = match.get('port')
                org = match.get('org', 'Unknown')
                product = match.get('product', '')
                
                # Format as shop-like URL
                result_url = f"http://{ip}:{port}" if port != 80 else f"http://{ip}"
                results.append({
                    'url': result_url,
                    'ip': ip,
                    'port': port,
                    'org': org,
                    'product': product
                })
            
            print(f"[SHODAN] Found {len(results)} results for query: {query[:50]}...")
            return results
        elif response.status_code == 401:
            print("[ERROR] Invalid Shodan API key")
        elif response.status_code == 429:
            print("[ERROR] Shodan API rate limit exceeded")
        else:
            print(f"[ERROR] Shodan API error: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Shodan search failed: {str(e)}")
    
    return []

# Load Shodan dorks (different syntax from Google)
def load_shodan_dorks(filename="inputDork/shodan_dorks.txt"):
    """Load Shodan-specific queries (different from Google dorks)"""
    queries = []
    
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        queries.append(line)
            print(f"[✓] Loaded {len(queries)} Shodan queries from {filename}")
            return queries
        except Exception as e:
            print(f"[ERROR] Failed to load Shodan dorks: {str(e)}")
    else:
        print(f"[WARNING] Shodan dorks file not found: {filename}")
    
    return []

def get_proxy_pagodo_style(proxy_list):
    """Pagodo-style round-robin proxy rotation"""
    global harvester_state
    
    if not proxy_list or proxy_list == [""]:
        return None
    
    proxy_index = harvester_state["proxy_rotation_index"] % len(proxy_list)
    proxy = proxy_list[proxy_index]
    harvester_state["proxy_rotation_index"] += 1
    
    return proxy

def generate_delay_list(min_delay=15, max_delay=45, count=20):
    """Generate Pagodo-style intelligent delay list
    
    Creates 20 random delay values between min and max,
    rounded to tenths place and sorted for variety.
    """
    delay_list = sorted(
        list(
            map(
                lambda x: round(x, 1),
                [random.uniform(min_delay, max_delay) for _ in range(count)]
            )
        )
    )
    return delay_list

def is_false_positive_url(url):
    """Pagodo-style false positive URL filtering
    
    Filters out non-shop URLs like exploit-db, cert.org, wikipedia, etc.
    """
    import re
    
    # Pagodo's ignore list + e-commerce specific filters
    ignore_url_patterns = [
        r"exploit-db\.com",
        r"kb\.cert\.org",
        r"twitter\.com/ExploitDB",
        r"wikipedia\.org",
        r"github\.com",
        r"stackoverflow\.com",
        r"reddit\.com",
        r"youtube\.com",
        r"facebook\.com",
        r"linkedin\.com",
        r"instagram\.com",
        r"wordpress\.org",
        r"w3\.org",
    ]
    
    for pattern in ignore_url_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    
    return False

def flaresolverr_request(url, max_timeout=150000):
    """Use FlareSolverr to bypass CAPTCHA and get HTML content"""
    import os
    
    use_flaresolverr = os.getenv("USE_FLARESOLVERR", "false").lower() == "true"
    flaresolverr_url = os.getenv("FLARESOLVERR_URL", "http://localhost:8191/v1")
    
    if not use_flaresolverr:
        return False, None, "FlareSolverr disabled"
    
    try:
        payload = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": max_timeout
        }
        
        response = requests.post(flaresolverr_url, json=payload, timeout=180)
        data = response.json()
        
        if data.get("status") == "ok":
            solution = data.get("solution", {})
            html = solution.get("response")
            print(f"[FlareSolverr] ✓ Successfully bypassed CAPTCHA for {url[:50]}...")
            return True, html, None
        else:
            error_msg = data.get("message", "Unknown error")
            print(f"[FlareSolverr] ✗ Failed: {error_msg}")
            return False, None, error_msg
            
    except Exception as e:
        print(f"[FlareSolverr] ✗ Exception: {str(e)}")
        return False, None, str(e)

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
    if config["engines"].get("shodan"):
        engines_to_use.append("shodan")
    
    for engine in engines_to_use:
        if harvester_state["stop_flag"]:
            break
            
        harvester_state["current_engine"] = engine
        
        # Special handling for Shodan (API-based, not web scraping)
        if engine == "shodan":
            import os
            api_key = os.getenv("SHODAN_API_KEY")
            if not api_key:
                print(f"[ERROR] SHODAN_API_KEY not found in .env file")
                print(f"[ERROR] Add SHODAN_API_KEY=your_key_here to .env")
                continue
            
            # Shodan API search (max 100 pages, 100 results each = 10,000 results)
            max_pages = 10  # Free tier: 100 results/month, Paid: unlimited
            for page_num in range(1, max_pages + 1):
                if harvester_state["stop_flag"]:
                    break
                
                print(f"[Shodan] Page {page_num}: Searching for '{dork[:50]}...'")
                results = search_shodan(dork, api_key, page=page_num)
                
                if not results:
                    print(f"[Shodan] Page {page_num}: No results found")
                    break  # No more results
                
                new_shops_found = 0
                for result in results:
                    if harvester_state["stop_flag"]:
                        break
                    
                    # Shodan returns IP:Port combinations
                    shop_url = result.get('url', '')
                    if shop_url:
                        is_new = check_and_insert_shop(shop_url, "shodan")
                        if is_new:
                            harvester_state["shops_found"] += 1
                            harvester_state["recent_shops"].insert(0, shop_url)
                            new_shops_found += 1
                            
                            if len(harvester_state["recent_shops"]) > 50:
                                harvester_state["recent_shops"] = harvester_state["recent_shops"][:50]
                            
                            ip = result.get('ip', 'N/A')
                            port = result.get('port', 'N/A')
                            org = result.get('org', 'N/A')
                            print(f"[+] SHODAN - Found: {shop_url} (IP: {ip}, Port: {port}, Org: {org[:30]}...)")
                
                if new_shops_found == 0:
                    print(f"[Shodan] Page {page_num}: No new shops, stopping pagination")
                    break
                
                # Delay between Shodan API requests (rate limiting)
                time.sleep(1)
            
            continue  # Skip normal web scraping logic for Shodan
        
        # Normal web scraping logic for other engines
        # Auto-stop logic
        max_empty_pages = 3  # Stop after 3 consecutive pages with no new shops
        empty_page_count = 0
        max_pages = 100  # Hard limit to prevent infinite loops
        
        for page_num in range(max_pages):
            page = page_num * 10  # Convert to offset (0, 10, 20, ...)
            
            if harvester_state["stop_flag"]:
                break
                
            urls = {
                "duckduckgo": f"https://duckduckgo.com/html/?q={requests.utils.quote(dork)}&s={page}",  # Added pagination param
                "google": f"https://www.google.com/search?q={requests.utils.quote(dork)}&start={page}",
                "bing": f"https://www.bing.com/search?q={requests.utils.quote(dork)}&first={page+1}",
                "yandex": f"https://yandex.com/search/?text={requests.utils.quote(dork)}&p={page_num}"
            }
            
            try:
                # Step 1: Try direct request FIRST (fast, no overhead)
                max_retries = 3
                retry_delay = 5
                html_content = None
                captcha_detected_on_direct = False
                
                for retry in range(max_retries):
                    try:
                        proxy_dict = None
                        if config.get("use_proxies"):
                            proxy = get_proxy()
                            if proxy:
                                proxy_dict = {"https": f"socks5://{proxy}"}
                        
                        # Direct request for all engines with VPN IP
                        print(f"[→] {engine} page {page_num}: Trying direct request...")
                        r = requests.get(urls[engine], headers=headers, proxies=proxy_dict, timeout=30)
                        html_content = r.text
                        
                        # Quick CAPTCHA check on direct response
                        response_lower = html_content.lower()
                        if (("cloudflare" in response_lower and "turnstile" in response_lower) or
                            ("smartcaptcha" in response_lower) or
                            ("recaptcha" in response_lower) or
                            ("unfortunately, bots use duckduckgo too" in response_lower)):
                            
                            print(f"[!] {engine} page {page_num}: CAPTCHA detected on direct request")
                            captcha_detected_on_direct = True
                            break  # Exit retry loop to try FlareSolverr
                        
                        # Success - no CAPTCHA
                        print(f"[✓] {engine} page {page_num}: Direct request successful")
                        break  # Success, exit retry loop
                        
                    except requests.exceptions.Timeout:
                        if retry < max_retries - 1:
                            print(f"[WARNING] {engine} page {page_num}: Timeout (attempt {retry+1}/{max_retries}), retrying in {retry_delay}s...")
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                        else:
                            print(f"[ERROR] {engine} page {page_num}: Max retries exceeded")
                            # Save error debug file
                            os.makedirs("logs", exist_ok=True)
                            debug_file = f"logs/debug_{engine}_page{page_num}_TIMEOUT.txt"
                            with open(debug_file, "w", encoding="utf-8") as f:
                                f.write(f"Timeout error after {max_retries} attempts\n")
                                f.write(f"URL: {urls.get(engine, 'N/A')}\n")
                            raise
                    
                    except Exception as e:
                        print(f"[ERROR] {engine} page {page_num}: {str(e)}")
                        os.makedirs("logs", exist_ok=True)
                        debug_file = f"logs/debug_{engine}_page{page_num}_ERROR.txt"
                        with open(debug_file, "w", encoding="utf-8") as f:
                            f.write(f"Error: {str(e)}\n")
                            f.write(f"Type: {type(e).__name__}\n")
                        if retry < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            raise
                
                # Step 2: If CAPTCHA detected, try FlareSolverr (only for Google/Yandex)
                if captcha_detected_on_direct and engine in ["google", "yandex"]:
                    print(f"[🔧] {engine} page {page_num}: Switching to FlareSolverr bypass...")
                    success, html, error = flaresolverr_request(urls[engine])
                    if success and html:
                        html_content = html
                        print(f"[✓] {engine} page {page_num}: FlareSolverr bypass successful")
                    else:
                        print(f"[✗] {engine} page {page_num}: FlareSolverr failed: {error}")
                        html_content = None
                
                if html_content is None:
                    continue  # Skip this page if all attempts failed
                
                # DEBUG: Save HTML response to file for inspection
                os.makedirs("logs", exist_ok=True)
                debug_file = f"logs/debug_{engine}_page{page_num}.html"
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(html_content)
                print(f"[DEBUG] {engine} page {page_num}: Length {len(html_content)} bytes, Saved to {debug_file}")
                
                # CAPTCHA detection (Cloudflare, Yandex SmartCaptcha, Google reCAPTCHA, DuckDuckGo Bot Challenge)
                response_lower = html_content.lower()
                captcha_detected = False
                captcha_type = ""
                
                if "unfortunately, bots use duckduckgo too" in response_lower or "anomaly-modal" in response_lower:
                    captcha_detected = True
                    captcha_type = "DuckDuckGo Bot Challenge (Image Puzzle)"
                elif "cloudflare" in response_lower and "turnstile" in response_lower:
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
                    if engine == "duckduckgo":
                        print(f"[ERROR] DuckDuckGo requires image puzzle CAPTCHA - Cannot bypass with FlareSolverr")
                        print(f"[RECOMMENDATION] Switch to Google engine with FlareSolverr enabled")
                    else:
                        print(f"[ERROR] Cannot bypass CAPTCHA - Enable FlareSolverr or switch engines")
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
                        
                        # Pagodo-style false positive filtering
                        if is_false_positive_url(shop):
                            print(f"[FILTER] Removing false positive URL: {shop[:80]}...")
                            continue
                        
                        # Filter valid shop URLs
                        if shop.startswith('http') and len(shop) > 15:
                            # Skip common non-shop domains
                            skip_domains = ['facebook.com', 'twitter.com', 'youtube.com', 'linkedin.com', 
                                          'instagram.com', 'github.com', 'wordpress.org', 'w3.org', 
                                          'wikipedia.org']
                            
                            is_blocked = any(domain in shop.lower() for domain in skip_domains)
                            
                            if not is_blocked:
                                # Use SQLite for duplicate checking and storage
                                is_new = check_and_insert_shop(shop, engine)
                                
                                if is_new:
                                    harvester_state["shops_found"] += 1
                                    harvester_state["recent_shops"].insert(0, shop)
                                    new_shops_found += 1
                                    
                                    # Keep only last 50 recent shops
                                    if len(harvester_state["recent_shops"]) > 50:
                                        harvester_state["recent_shops"] = harvester_state["recent_shops"][:50]
                                    
                                    print(f"[+] {engine.upper()} - Shop found: {shop}")
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
            
            # Pagodo-style intelligent delay (variable timing)
            if harvester_state["delay_list"] and page_num > 0:
                pause_time = random.choice(harvester_state["delay_list"])
                print(f"[INFO] Sleeping {pause_time}s before next page (intelligent delay)...")
                time.sleep(pause_time)
            else:
                # Fallback to simple delay if delay_list not initialized
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
    clear_results = request.get("clear_results", False)  # Default: append mode
    
    # Create outputDork directory
    os.makedirs("outputDork", exist_ok=True)
    
    # Get selected engines
    selected_engines = []
    if request.get("engines", {}).get("duckduckgo"):
        selected_engines.append("duckduckgo")
    if request.get("engines", {}).get("google"):
        selected_engines.append("google")
    if request.get("engines", {}).get("bing"):
        selected_engines.append("bing")
    if request.get("engines", {}).get("yandex"):
        selected_engines.append("yandex")
    if request.get("engines", {}).get("shodan"):
        selected_engines.append("shodan")
    
    if clear_results:
        # Clear mode: delete shops from database for selected engines
        for engine in selected_engines:
            clear_shops_by_engine(engine)
    else:
        # Append mode: SQLite handles duplicates automatically via UNIQUE constraint
        print(f"[✓] Append mode: SQLite will skip duplicates automatically")
    
    # Reset state (no need to load existing shops - SQLite handles it)
    harvester_state = {
        "status": "running",
        "shops_found": 0,
        "active_threads": 0,
        "current_engine": "",
        "recent_shops": [],
        "stop_flag": False,
        "config": request,
        "proxy_rotation_index": 0,
        "delay_list": []
    }
    
    # Initialize Pagodo-style intelligent delay list
    min_delay = request.get("min_delay", 15)
    max_delay = request.get("max_delay", 45)
    harvester_state["delay_list"] = generate_delay_list(min_delay, max_delay, 20)
    print(f"[✓] Generated delay list: {min_delay}-{max_delay}s")
    
    # Load dorks (GHDB or custom)
    use_ghdb = request.get("use_ghdb", False)
    ghdb_category = request.get("ghdb_category", "all")
    use_shodan = request.get("engines", {}).get("shodan", False)
    
    if use_shodan:
        # Shodan uses different dorks file (API-based queries)
        dorks_to_use = load_shodan_dorks("inputDork/shodan_dorks.txt")
        print(f"[✓] Using Shodan queries: {len(dorks_to_use)}")
    elif use_ghdb:
        dorks_to_use = load_dorks_from_file(
            filename="inputDork/general_search_dorks.txt",
            use_ghdb=True,
            ghdb_category=ghdb_category
        )
        print(f"[✓] Using GHDB dorks: {len(dorks_to_use)} from category '{ghdb_category}'")
    else:
        dork_count = min(request.get("dork_count", 50), len(DORKS))
        dorks_to_use = DORKS[:dork_count]
        print(f"[✓] Using custom dorks: {len(dorks_to_use)}")
    
    thread_count = request.get("thread_count", 10)
    # Safety: Limit threads when using many dorks
    if len(dorks_to_use) > 100 and thread_count > 5:
        thread_count = 5
        print(f"[WARNING] Large dork count ({len(dorks_to_use)}), limiting threads to {thread_count}")
    
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
        
        # Export shops from database to text files
        print("[✓] Harvesting completed. Exporting to files...")
        for engine in selected_engines:
            output_file = f"outputDork/shops_fresh_2025_{engine}.txt"
            export_shops_to_file(engine, output_file)
        
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
