import os
from datetime import datetime

def save_report(content: str, mode: str, fund_name: str = "Summary", fund_code: str = ""):
    """
    Save the report to a markdown file in the reports/ directory.
    Naming format: YYYY-MM-DD_{mode}_{fund_code}_{fund_name}.md
    """
    today = datetime.now().strftime("%Y-%m-%d")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    report_dir = os.path.join(base_dir, "reports")
    
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    
    # Sanitize filenames
    safe_name = "".join([c for c in fund_name if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).strip()
    
    if fund_code:
        filename = f"{today}_{mode}_{fund_code}_{safe_name}.md"
    else:
        filename = f"{today}_{mode}_SUMMARY.md"
        
    filepath = os.path.join(report_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Report saved to: {filepath}")
    return filepath
