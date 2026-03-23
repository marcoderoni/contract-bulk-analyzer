# Copyright (c) 2025 Marco De Roni. All rights reserved.
import re

def scan_clauses(contracts, clauses):
    results = {}
    total = len(contracts)
    for clause in clauses:
        name = clause["name"]
        keywords = clause["keywords"]
        present_in, absent_in = [], []
        for filename, text in contracts.items():
            found = any(re.search(re.escape(kw), text, re.IGNORECASE) for kw in keywords)
            (present_in if found else absent_in).append(filename)
        results[name] = {
            "clause": name, "keywords": keywords,
            "present_count": len(present_in), "absent_count": len(absent_in),
            "total": total,
            "presence_pct": round(len(present_in)/total*100, 1) if total > 0 else 0,
            "present_in": present_in, "absent_in": absent_in,
        }
    return results
