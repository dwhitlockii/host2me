import os
from datetime import datetime

def write_log(message: str) -> None:
    os.makedirs("./output", exist_ok=True)
    log_filename = f"./output/scrape_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    with open(log_filename, "a", encoding="utf-8") as f:
        f.write(f"{message}\n")

def verify_company_record(company: dict) -> bool:
    reasons = []
    website_url = company.get("website_url") or company.get("Website URL") or company.get("url")
    if not website_url:
        reasons.append("Missing website URL")

    careers_page = company.get("careers_page_url") or company.get("Careers Page URL") or company.get("careers_url")
    if not careers_page:
        reasons.append("No careers page found")

    if not company.get("us_based", True):
        reasons.append("Company not U.S.-based")

    if company.get("is_reseller", False):
        reasons.append("Detected as reseller/affiliate")

    if not company.get("primary_hosting", True):
        reasons.append("Hosting not a primary service")

    if reasons:
        log_msg = f"❌ REJECTED: {company.get('company_name') or company.get('Company Name', 'Unknown')} - Reason(s): {', '.join(reasons)}"
        print(log_msg)
        write_log(log_msg)
        return False
    else:
        log_msg = f"✅ SAVED: {company.get('company_name') or company.get('Company Name', 'Unknown')} - Passed all filters"
        print(log_msg)
        write_log(log_msg)
        return True
