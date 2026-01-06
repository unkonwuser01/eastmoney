import os
import sys
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import glob

# Ensure src is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.analysis.pre_market import PreMarketAnalyst
from src.analysis.post_market import PostMarketAnalyst
from src.storage.db import init_db, get_active_funds, get_all_funds, upsert_fund, delete_fund, get_fund_by_code
from src.scheduler.manager import scheduler_manager
from src.report_gen import save_report
from src.data_sources.akshare_api import get_all_fund_list
from datetime import datetime

# --- Startup/Shutdown ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing Database...")
    init_db()
    print("Starting Scheduler...")
    scheduler_manager.start()
    yield
    # Shutdown logic if needed

app = FastAPI(title="EastMoney Report API", lifespan=lifespan)

# Configure CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(BASE_DIR, "reports")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
ENV_FILE = os.path.join(BASE_DIR, ".env")
MARKET_FUNDS_CACHE = os.path.join(CONFIG_DIR, "market_funds_cache.json")

# --- Models ---

class ReportSummary(BaseModel):
    filename: str
    date: str
    mode: str # 'pre' or 'post'
    fund_code: Optional[str] = None
    fund_name: Optional[str] = None
    is_summary: bool = True # True if it's a run_all report or Summary

class FundItem(BaseModel):
    code: str
    name: str
    style: Optional[str] = "Unknown"
    focus: Optional[List[str]] = []
    pre_market_time: Optional[str] = None # HH:MM
    post_market_time: Optional[str] = None # HH:MM
    is_active: bool = True

class SettingsUpdate(BaseModel):
    llm_provider: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None

class GenerateRequest(BaseModel):
    fund_code: Optional[str] = None

# --- Helpers ---
def load_env_file():
    env_vars = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

def save_env_file(updates: Dict[str, str]):
    # Read existing lines to preserve comments/order
    lines = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    
    # Map of key -> line_index
    key_map = {}
    for i, line in enumerate(lines):
        if line.strip() and not line.strip().startswith("#") and "=" in line:
            k = line.split("=", 1)[0].strip()
            key_map[k] = i
    
    for key, value in updates.items():
        if value is None: continue # Skip if not provided
        
        new_line = f"{key}={value}\n"
        if key in key_map:
            lines[key_map[key]] = new_line
        else:
            lines.append(new_line)
            
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)

# --- Endpoints ---

@app.get("/api/reports", response_model=List[ReportSummary])
async def list_reports():
    if not os.path.exists(REPORT_DIR):
        return []
    
    # Load funds for name mapping
    fund_map = {}
    try:
        funds = get_all_funds()
        for f in funds:
            fund_map[f['code']] = f['name']
    except:
        pass

    reports = []
    files = glob.glob(os.path.join(REPORT_DIR, "*_report.md"))
    files.sort(key=os.path.getmtime, reverse=True) # Newest first
    
    for f in files:
        filename = os.path.basename(f)
        try:
            # Expected formats:
            # 1. YYYY-MM-DD_mode_SUMMARY.md
            # 2. YYYY-MM-DD_mode_CODE_NAME.md
            
            parts = filename.replace("_report.md", "").split("_")
            if len(parts) < 2: continue
            
            date_str = parts[0]
            mode = parts[1]
            
            if "SUMMARY" in filename:
                 reports.append(ReportSummary(
                    filename=filename, 
                    date=date_str, 
                    mode=mode,
                    is_summary=True,
                    fund_name="Market Overview"
                ))
            else:
                 # Try to extract code. Assuming format YYYY-MM-DD_mode_CODE_NAME.md
                 # If we used the new save_report function in src/report_gen.py
                 if len(parts) >= 3:
                     code = parts[2]
                     name = fund_map.get(code, code)
                     reports.append(ReportSummary(
                        filename=filename, 
                        date=date_str, 
                        mode=mode, 
                        fund_code=code,
                        fund_name=name,
                        is_summary=False
                    ))
        except Exception as e:
            print(f"Error parsing filename {filename}: {e}")
            continue
            
    return reports

@app.get("/api/reports/{filename}")
async def get_report(filename: str):
    filepath = os.path.join(REPORT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report not found")
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    return {"content": content}

@app.get("/api/market-funds")
async def search_market_funds(query: str = ""):
    funds = []
    
    # Check cache
    if os.path.exists(MARKET_FUNDS_CACHE):
        # Check modified time (e.g. 24h)
        try:
            mtime = os.path.getmtime(MARKET_FUNDS_CACHE)
            if (datetime.now().timestamp() - mtime) < 86400:
                with open(MARKET_FUNDS_CACHE, 'r', encoding='utf-8') as f:
                    funds = json.load(f)
        except Exception as e:
            print(f"Cache read error: {e}")
    
    # If no funds from cache, fetch
    if not funds:
        print("Fetching fresh fund list from AkShare...")
        funds = get_all_fund_list()
        # Cache it
        if funds:
            try:
                if not os.path.exists(CONFIG_DIR):
                    os.makedirs(CONFIG_DIR)
                with open(MARKET_FUNDS_CACHE, 'w', encoding='utf-8') as f:
                    json.dump(funds, f, ensure_ascii=False)
            except Exception as e:
                print(f"Cache write error: {e}")
            
    # Filter
    if not query:
        return funds[:20] # Return top 20 if no query
        
    query = query.lower()
    results = []
    for f in funds:
        # Match code (startswith) or name (contains) or pinyin (contains)
        # Safe access with .get()
        f_code = str(f.get('code', ''))
        f_name = str(f.get('name', ''))
        f_pinyin = str(f.get('pinyin', ''))
        
        if (f_code.startswith(query) or 
            query in f_name.lower() or 
            query in f_pinyin.lower()):
            results.append(f)
            
            if len(results) >= 50: # Limit results
                break
                
    return results

@app.post("/api/generate/{mode}")
async def generate_report_endpoint(mode: str, request: GenerateRequest = None):
    if mode not in ["pre", "post"]:
        raise HTTPException(status_code=400, detail="Invalid mode. Use 'pre' or 'post'.")
    
    fund_code = request.fund_code if request else None

    try:
        print(f"Generating {mode}-market report... (Fund: {fund_code if fund_code else 'ALL'})")
        
        # Use Scheduler's worker logic to execute immediately
        if fund_code:
            scheduler_manager.run_analysis_task(fund_code, mode)
            return {"status": "success", "message": f"Task triggered for {fund_code}"}
        else:
            # If generating for ALL funds (Manual Trigger)
            # We can iterate and run them
            funds = get_active_funds()
            results = []
            for fund in funds:
                try:
                    scheduler_manager.run_analysis_task(fund['code'], mode)
                    results.append(fund['code'])
                except:
                    pass
            return {"status": "success", "message": f"Triggered tasks for {len(results)} funds"}
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/funds", response_model=List[FundItem])
async def get_funds_endpoint():
    try:
        funds = get_all_funds()
        # Convert JSON string focus to list if needed, DB layer handles dict conversion but 'focus' might be string
        result = []
        for f in funds:
            item = dict(f)
            if isinstance(item.get('focus'), str):
                try:
                    item['focus'] = json.loads(item['focus'])
                except:
                    item['focus'] = []
            
            # Convert SQLite Row to dict fully
            result.append(FundItem(
                code=item['code'],
                name=item['name'],
                style=item.get('style'),
                focus=item['focus'],
                pre_market_time=item.get('pre_market_time'),
                post_market_time=item.get('post_market_time'),
                is_active=bool(item.get('is_active', True))
            ))
        return result
    except Exception as e:
        print(f"Error reading funds: {e}")
        return []

@app.post("/api/funds")
async def save_fund_endpoint(fund: FundItem):
    try:
        fund_data = fund.model_dump()
        upsert_fund(fund_data)
        
        # Sync with scheduler
        scheduler_manager.add_fund_jobs(fund_data)
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/funds/{code}")
async def delete_fund_endpoint(code: str):
    try:
        delete_fund(code)
        
        # Sync with scheduler
        scheduler_manager.remove_fund_jobs(code)
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings")
async def get_settings():
    env = load_env_file()
    def mask(key):
        val = env.get(key, "")
        if len(val) > 8:
            return val[:4] + "..." + val[-4:]
        return val
    
    return {
        "llm_provider": env.get("LLM_PROVIDER", "gemini"),
        "gemini_api_key_masked": mask("GEMINI_API_KEY"),
        "openai_api_key_masked": mask("OPENAI_API_KEY"),
        "tavily_api_key_masked": mask("TAVILY_API_KEY")
    }

@app.post("/api/settings")
async def update_settings(settings: SettingsUpdate):
    updates = {}
    if settings.llm_provider:
        updates["LLM_PROVIDER"] = settings.llm_provider
    if settings.gemini_api_key:
        updates["GEMINI_API_KEY"] = settings.gemini_api_key
    if settings.openai_api_key:
        updates["OPENAI_API_KEY"] = settings.openai_api_key
    if settings.tavily_api_key:
        updates["TAVILY_API_KEY"] = settings.tavily_api_key
        
    save_env_file(updates)
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    # Need to run init_db if running directly without lifespan
    init_db()
    scheduler_manager.start()
    uvicorn.run(app, host="0.0.0.0", port=8000)