# Copyright (c) 2025 Marco De Roni. All rights reserved.
# Licensed under the MIT License — see LICENSE file for details.

import re


def assign_groups(contracts: dict, groups_config: list) -> dict:
    """
    Assegna ogni contratto a un gruppo in base ai pattern nel filename.
    Restituisce dict {filename: group_name}.
    """
    assignments = {}

    for filename in contracts.keys():
        assigned = False
        for group in groups_config:
            patterns = group.get("patterns", [])
            for pattern in patterns:
                if re.search(re.escape(pattern), filename, re.IGNORECASE):
                    assignments[filename] = group["name"]
                    assigned = True
                    break
            if assigned:
                break
        if not assigned:
            assignments[filename] = "Other"

    return assignments


def compare_groups(
    contracts: dict,
    clause_results: dict,
    groups_config: list
) -> dict:
    """
    Confronta la presenza di clausole tra gruppi diversi di contratti.
    Evidenzia clausole presenti in un gruppo ma non nell'altro.
    """
    assignments = assign_groups(contracts, groups_config)

    # Raggruppa i contratti per gruppo
    grouped = {}
    for filename, group in assignments.items():
        grouped.setdefault(group, []).append(filename)

    # Per ogni clausola, calcola % presenza per gruppo
    comparison = {}
    for clause_name, clause_data in clause_results.items():
        comparison[clause_name] = {}
        present_set = set(clause_data["present_in"])

        for group_name, filenames in grouped.items():
            if not filenames:
                continue
            present_in_group = [f for f in filenames if f in present_set]
            pct = round(len(present_in_group) / len(filenames) * 100, 1)
            comparison[clause_name][group_name] = {
                "present": len(present_in_group),
                "total": len(filenames),
                "percentage": pct,
                "files": present_in_group,
            }

    # Identifica divergenze significative (>30% di differenza tra gruppi)
    divergences = []
    group_names = list(grouped.keys())

    for clause_name, group_data in comparison.items():
        pcts = {g: group_data[g]["percentage"] for g in group_data}
        if len(pcts) >= 2:
            max_pct = max(pcts.values())
            min_pct = min(pcts.values())
            if max_pct - min_pct >= 30:
                divergences.append({
                    "clause": clause_name,
                    "max_group": max(pcts, key=pcts.get),
                    "max_pct": max_pct,
                    "min_group": min(pcts, key=pcts.get),
                    "min_pct": min_pct,
                    "gap": round(max_pct - min_pct, 1),
                })

    return {
        "assignments": assignments,
        "grouped": grouped,
        "comparison": comparison,
        "divergences": sorted(divergences, key=lambda x: x["gap"], reverse=True),
    }