import os
import sys
import json
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import glob

# Ensure src is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.analysis.pre_market import PreMarketAnalyst
from src.analysis.post_market import PostMarketAnalyst

app = FastAPI(title="EastMoney Report API")

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
FUNDS_FILE = os.path.join(CONFIG_DIR, "funds.json")
ENV_FILE = os.path.join(BASE_DIR, ".env")

class ReportSummary(BaseModel):
    filename: str
    date: str
    mode: str # 'pre' or 'post'
    fund_code: Optional[str] = None
    fund_name: Optional[str] = None
    is_summary: bool = True # True if it's a run_all report, False if specific fund

class FundItem(BaseModel):
    code: str
    name: str
    style: Optional[str] = "Unknown"
    focus: Optional[List[str]] = []

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
    if os.path.exists(FUNDS_FILE):
        try:
            with open(FUNDS_FILE, "r", encoding="utf-8") as f:
                funds_data = json.load(f)
                for fund in funds_data:
                    fund_map[fund["code"]] = fund["name"]
        except:
            pass

    reports = []
    # Pattern matching for YYYY-MM-DD_mode_report.md OR YYYY-MM-DD_mode_code_report.md
    files = glob.glob(os.path.join(REPORT_DIR, "*_report.md"))
    files.sort(key=os.path.getmtime, reverse=True) # Newest first
    
    for f in files:
        filename = os.path.basename(f)
        try:
            # Expected formats:
            # 1. 2026-01-05_pre_report.md (Summary) -> parts len 3
            # 2. 2026-01-05_pre_005827_report.md (Specific) -> parts len 4
            
            parts = filename.replace("_report.md", "").split("_")
            
            if len(parts) < 2: continue
            
            date_str = parts[0]
            mode = parts[1]
            
            if len(parts) == 2:
                # Summary report
                reports.append(ReportSummary(
                    filename=filename, 
                    date=date_str, 
                    mode=mode,
                    is_summary=True,
                    fund_name="Market Overview"
                ))
            elif len(parts) == 3:
                # Specific fund report
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

@app.post("/api/generate/{mode}")
async def generate_report(mode: str, request: GenerateRequest = None):
    if mode not in ["pre", "post"]:
        raise HTTPException(status_code=400, detail="Invalid mode. Use 'pre' or 'post'.")
    
    fund_code = request.fund_code if request else None

    try:
        print(f"Generating {mode}-market report... (Fund: {fund_code if fund_code else 'ALL'})")
        if mode == "pre":
            analyst = PreMarketAnalyst()
            if fund_code:
                report_content = analyst.run_one(fund_code)
            else:
                report_content = analyst.run_all()
        else:
            analyst = PostMarketAnalyst()
            if fund_code:
                report_content = analyst.run_one(fund_code)
            else:
                report_content = analyst.run_all()
        
        today = os.path.basename(os.path.abspath(__file__)) # dummy
        from datetime import datetime
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        if not os.path.exists(REPORT_DIR):
            os.makedirs(REPORT_DIR)
        
        # If single fund, append to filename or specific logic?
        # For simplicity, we just save it as a separate file or append.
        # But user might want to view it.
        # Let's save as `YYYY-MM-DD_{mode}_{code}_report.md` if single, else default.
        
        if fund_code:
            filename = f"{today_str}_{mode}_{fund_code}_report.md"
        else:
            filename = f"{today_str}_{mode}_report.md"
            
        filepath = os.path.join(REPORT_DIR, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        return {"status": "success", "filename": filename, "content": report_content}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/funds", response_model=List[FundItem])
async def get_funds():
    if not os.path.exists(FUNDS_FILE):
        return []
    try:
        with open(FUNDS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except Exception as e:
        print(f"Error reading funds: {e}")
        return []

@app.post("/api/funds")
async def save_funds(funds: List[FundItem]):
    try:
        with open(FUNDS_FILE, "w", encoding="utf-8") as f:
            # Convert pydantic models to dicts
            json.dump([item.model_dump() for item in funds], f, ensure_ascii=False, indent=2)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings")
async def get_settings():
    env = load_env_file()
    # Return masked keys for security
    def mask(key):
        val = env.get(key, "")
        if len(val) > 8:
            return val[:4] + "..." + val[-4:]
        return val # Too short to mask meaningfully or empty
    
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
