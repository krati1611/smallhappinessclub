from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
import os
import requests

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Load known IPs from ip_list.json
with open("ip_list.json", "r") as file:
    known_ips = set(json.load(file)["ips"])

# Load previously logged IPs (if file exists)
LOG_FILE = "logged_ips.json"
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "r") as file:
        all_ips = set(json.load(file)["logged_ips"])
else:
    all_ips = set()

def save_ips():
    """Save logged IPs to a JSON file for persistence."""
    with open(LOG_FILE, "w") as file:
        json.dump({"logged_ips": list(all_ips)}, file, indent=4)

def crawler_detect(user_agent: str) -> bool:
    crawlers = [
        'Google', 'Googlebot', 'google', 'msnbot', 'Rambler', 'Yahoo', 
        'AbachoBOT', 'Accoona', 'AcoiRobot', 'ASPSeek', 'CrocCrawler', 
        'Dumbot', 'FAST-WebCrawler', 'GeonaBot', 'Gigabot', 'Lycos', 
        'MSRBOT', 'Scooter', 'Altavista', 'IDBot', 'eStyle', 'Scrubby', 
        'facebookexternalhit', 'python', 'LoiLoNote', 'quic', 'Go-http', 
        'webtech', 'WhatsApp'
    ]
    
    crawlers_agents = '|'.join(crawlers)
    return user_agent not in crawlers_agents

async def is_user_from_usa(ip_address: str) -> bool:
    try:
        api_url = f"http://ip-api.com/json/{ip_address}"
        response = requests.get(api_url)
        ip_data = response.json()
        return ip_data.get('countryCode', '').upper() == "US"
    except:
        return False

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    query_params = request.query_params
    
    # Get query parameters these are custom parameters set in final url of campaign
    gclid = query_params.get("gclid")
    campaignid = query_params.get("campaignid")
    placement = query_params.get("placement")
    network = query_params.get("network")
    random = query_params.get("random")
    
    # Check conditions
    is_from_google_ads = gclid is not None
    user_agent = request.headers.get('user-agent', '')
    is_windows_desktop = 'Windows' in user_agent
    
    # Check if user is from USA (only when coming from Google Ads)
    client_host = request.client.host
    is_usa = is_from_google_ads and await is_user_from_usa(client_host)
    
    # Check additional parameters
    additional_params_condition = all([
        is_from_google_ads, 
        is_usa, 
        is_windows_desktop, 
        campaignid, 
        placement, 
        random, 
        network
    ])
    
    # Bot detection
    user_agent_lower = user_agent.lower()
    is_bot = any([
        'bot' in user_agent_lower,
        'crawl' in user_agent_lower,
        'spider' in user_agent_lower,
        'slurp' in user_agent_lower
    ])
    
    # Log IP addresses
    ip = client_host
    if gclid:
        marked_ip = f"gclid_{ip}"
        if ip in all_ips:  # If IP was logged normally, remove it
            all_ips.discard(ip)
        all_ips.add(marked_ip)  # Store with gclid marker
    else:
        if f"gclid_{ip}" not in all_ips:  # Don't override if already marked
            all_ips.add(ip)

    save_ips()  # Save IPs to file
    
    # If IP is in known_ips list, show main.html directly
    if ip in known_ips:
        return templates.TemplateResponse("main.html", {"request": request})
    
    # Redirect condition
    if all([
        is_from_google_ads,
        is_usa,
        is_windows_desktop,
        campaignid,
        placement,
        random,
        network,
        not is_bot
    ]):
        try:
            return templates.TemplateResponse("main.html", {"request": request})
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="main.html not found")
    else:
        try:
            return templates.TemplateResponse("main.html", {"request": request})
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="main.html not found")

@app.get("/all-ips/")
async def get_all_ips():
    return {"logged_ips": list(all_ips)}

@app.get("/{page_name}", response_class=HTMLResponse)
async def serve_page(request: Request, page_name: str):
    if page_name in ["contact.html"]:
        return templates.TemplateResponse(page_name, {"request": request})
    return HTMLResponse("Page Not Found", status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
