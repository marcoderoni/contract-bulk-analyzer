# Copyright (c) 2025 Marco De Roni. All rights reserved.
import re

def extract_metadata(text, meta_config):
    result = {}
    for kw in meta_config.get("parties_keywords", []):
        m = re.search(rf"{re.escape(kw)}\s+([A-Z][^\n]{{5,80}})", text, re.IGNORECASE)
        if m: result["parties"] = m.group(1).strip(); break
    for kw in meta_config.get("date_keywords", []):
        m = re.search(rf"{re.escape(kw)}\s+([A-Z][a-z]{{2,8}}\s+\d{{1,2}},?\s+\d{{4}}|\d{{1,2}}[/\-\.]\d{{1,2}}[/\-\.]\d{{2,4}})", text, re.IGNORECASE)
        if m: result["effective_date"] = m.group(1).strip(); break
    for kw in meta_config.get("governing_law_keywords", []):
        m = re.search(rf"{re.escape(kw)}\s+(?:the\s+)?(?:laws?\s+of\s+)?([A-Z][a-zA-Z\s]{{3,40}})", text, re.IGNORECASE)
        if m: result["governing_law"] = m.group(1).strip(); break
    for kw in meta_config.get("jurisdiction_keywords", []):
        m = re.search(rf"{re.escape(kw)}\s+(?:of\s+)?([A-Z][a-zA-Z\s]{{3,40}})", text, re.IGNORECASE)
        if m: result["jurisdiction"] = m.group(1).strip(); break
    m = re.search(r"(\d+)\s+(?:business\s+)?days['\s]*\s*(?:prior\s+)?(?:written\s+)?notice", text, re.IGNORECASE)
    if m: result["notice_period"] = f"{m.group(1)} days"
    for kw in meta_config.get("duration_keywords", []):
        m = re.search(rf"{re.escape(kw)}\s+(?:of\s+)?(\d+\s+(?:months?|years?)|one year|two years|three years)", text, re.IGNORECASE)
        if m: result["duration"] = m.group(1).strip(); break
    for kw in meta_config.get("renewal_keywords", []):
        if re.search(re.escape(kw), text, re.IGNORECASE):
            result["auto_renewal"] = "Yes"; break
    if "auto_renewal" not in result: result["auto_renewal"] = "No"
    return result

def scan_metadata(contracts, meta_config):
    return {filename: extract_metadata(text, meta_config) for filename, text in contracts.items()}
