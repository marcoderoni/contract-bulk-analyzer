# Copyright (c) 2026 Marco De Roni. All rights reserved.
# Licensed under the MIT License — see LICENSE file for details.

import re


def extract_excerpt(text: str, keyword: str, context: int = 120) -> str:
    match = re.search(re.escape(keyword), text, re.IGNORECASE)
    if not match:
        return ""
    s = max(0, match.start() - context)
    e = min(len(text), match.end() + context)
    return f"...{text[s:e].strip()}..."


def confidence_score(count: int, percentage: float) -> str:
    if percentage >= 80 and count >= 2:
        return "HIGH"
    elif percentage >= 40 or count >= 1:
        return "MEDIUM"
    else:
        return "LOW"


def scan_keywords(contracts: dict, keywords: list) -> dict:
    results = {}
    total = len(contracts)

    for keyword in keywords:
        matches = []
        for filename, text in contracts.items():
            if re.search(re.escape(keyword), text, re.IGNORECASE):
                count = len(re.findall(re.escape(keyword), text, re.IGNORECASE))
                matches.append({
                    "filename": filename,
                    "count": count,
                    "excerpt": extract_excerpt(text, keyword),
                })

        pct = round(len(matches) / total * 100, 1) if total > 0 else 0
        total_count = sum(m["count"] for m in matches)

        results[keyword] = {
            "keyword": keyword,
            "contracts_found": len(matches),
            "contracts_total": total,
            "percentage": pct,
            "total_occurrences": total_count,
            "confidence": confidence_score(total_count, pct),
            "matches": matches,
        }

    return results