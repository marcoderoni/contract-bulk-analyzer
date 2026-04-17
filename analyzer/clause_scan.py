# Copyright (c) 2026 Marco De Roni. All rights reserved.
# Licensed under the MIT License — see LICENSE file for details.

import re


def extract_clause_text(text: str, keyword: str, context: int = 500) -> str:
    """
    Extracts the surrounding text around a keyword match.
    Tries to capture the full clause by looking for sentence boundaries.
    """
    match = re.search(re.escape(keyword), text, re.IGNORECASE)
    if not match:
        return ""

    # Expand context
    start = max(0, match.start() - context)
    end = min(len(text), match.end() + context)
    excerpt = text[start:end].strip()

    # Try to trim to sentence boundaries
    # Find first capital letter after start
    first_cap = re.search(r'[A-Z]', excerpt)
    if first_cap and first_cap.start() < 100:
        excerpt = excerpt[first_cap.start():]

    # Find last period before end
    last_period = excerpt.rfind(".")
    if last_period > len(excerpt) // 2:
        excerpt = excerpt[:last_period + 1]

    return excerpt.strip()


def scan_clauses(contracts: dict, clauses: list) -> dict:
    """
    For each clause, checks presence/absence in each contract.
    Also extracts the relevant text excerpt where found.
    """
    results = {}
    total = len(contracts)

    for clause in clauses:
        name = clause["name"]
        keywords = clause["keywords"]
        present_in = []
        absent_in = []
        extracts = {}  # filename -> extracted clause text

        for filename, text in contracts.items():
            found = False
            for kw in keywords:
                if re.search(re.escape(kw), text, re.IGNORECASE):
                    found = True
                    # Extract clause text for the first matching keyword
                    if filename not in extracts:
                        extract = extract_clause_text(text, kw)
                        if extract:
                            extracts[filename] = extract
                    break

            if found:
                present_in.append(filename)
            else:
                absent_in.append(filename)

        results[name] = {
            "clause": name,
            "keywords": keywords,
            "present_count": len(present_in),
            "absent_count": len(absent_in),
            "total": total,
            "presence_pct": round(len(present_in) / total * 100, 1) if total > 0 else 0,
            "present_in": present_in,
            "absent_in": absent_in,
            "extracts": extracts,
        }

    return results