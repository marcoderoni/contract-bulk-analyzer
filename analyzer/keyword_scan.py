# Copyright (c) 2025 Marco De Roni. All rights reserved.
# Licensed under the MIT License — see LICENSE file for details.

import re


def scan_keywords(contracts: dict, keywords: list) -> dict:
    """
    Per ogni keyword, conta in quanti contratti appare.
    Restituisce dict con statistiche aggregate.
    """
    results = {}
    total = len(contracts)

    for keyword in keywords:
        matches = []
        for filename, text in contracts.items():
            if re.search(re.escape(keyword), text, re.IGNORECASE):
                # Conta quante volte appare nel contratto
                count = len(re.findall(re.escape(keyword), text, re.IGNORECASE))
                matches.append({
                    "filename": filename,
                    "count": count,
                    "excerpt": extract_excerpt(text, keyword),
                })

        results[keyword] = {
            "keyword": keyword,
            "contracts_found": len(matches),
            "contracts_total": total,
            "percentage": round(len(matches) / total * 100, 1) if total > 0 else 0,
            "matches": matches,
        }

    return results


def extract_excerpt(text: str, keyword: str, context: int = 120) -> str:
    """Estrae un breve estratto attorno alla prima occorrenza del keyword."""
    match = re.search(re.escape(keyword), text, re.IGNORECASE)
    if not match:
        return ""
    start = max(0, match.start() - context)
    end = min(len(text), match.end() + context)
    return f"...{text[start:end].strip()}..."