# Copyright (c) 2025 Marco De Roni. All rights reserved.
import re

def extract_excerpt(text, keyword, context=120):
    match = re.search(re.escape(keyword), text, re.IGNORECASE)
    if not match: return ""
    s = max(0, match.start()-context)
    e = min(len(text), match.end()+context)
    return f"...{text[s:e].strip()}..."

def scan_keywords(contracts, keywords):
    results = {}
    total = len(contracts)
    for keyword in keywords:
        matches = []
        for filename, text in contracts.items():
            if re.search(re.escape(keyword), text, re.IGNORECASE):
                count = len(re.findall(re.escape(keyword), text, re.IGNORECASE))
                matches.append({"filename": filename, "count": count, "excerpt": extract_excerpt(text, keyword)})
        results[keyword] = {
            "keyword": keyword,
            "contracts_found": len(matches),
            "contracts_total": total,
            "percentage": round(len(matches)/total*100, 1) if total > 0 else 0,
            "matches": matches,
        }
    return results
