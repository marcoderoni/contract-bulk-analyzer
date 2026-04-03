# Copyright (c) 2026 Marco De Roni. All rights reserved.
# Licensed under the MIT License — see LICENSE file for details.

import os
import json
import hashlib
from datetime import datetime


AUDIT_LOG_PATH = "audit_log.jsonl"


def compute_hash(text: str) -> str:
    """Compute SHA256 hash of text for integrity verification."""
    return hashlib.sha256(text.encode()).hexdigest()


def log_analysis(
    contracts: list,
    keyword_results: dict,
    clause_results: dict,
    overall_score: str = None
):
    """Append an audit entry to the log file."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "contracts_analysed": contracts,
        "contracts_count": len(contracts),
        "keywords_searched": list(keyword_results.keys()),
        "clauses_checked": list(clause_results.keys()),
        "overall_scores": {
            name: data["presence_pct"]
            for name, data in clause_results.items()
        },
        "missing_clauses": [
            name for name, data in clause_results.items()
            if data["absent_count"] > 0
        ],
    }

    # Add hash for integrity
    entry_str = json.dumps(entry, sort_keys=True)
    entry["hash"] = compute_hash(entry_str)

    with open(AUDIT_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def read_audit_log() -> list:
    """Read and return all audit log entries."""
    if not os.path.exists(AUDIT_LOG_PATH):
        return []
    entries = []
    with open(AUDIT_LOG_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries