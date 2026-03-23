# Copyright (c) 2025 Marco De Roni. All rights reserved.
import re

def assign_groups(contracts, groups_config):
    assignments = {}
    for filename in contracts.keys():
        assigned = False
        for group in groups_config:
            for pattern in group.get("patterns", []):
                if re.search(re.escape(pattern), filename, re.IGNORECASE):
                    assignments[filename] = group["name"]; assigned = True; break
            if assigned: break
        if not assigned: assignments[filename] = "Other"
    return assignments

def compare_groups(contracts, clause_results, groups_config):
    assignments = assign_groups(contracts, groups_config)
    grouped = {}
    for filename, group in assignments.items():
        grouped.setdefault(group, []).append(filename)
    comparison = {}
    for clause_name, clause_data in clause_results.items():
        comparison[clause_name] = {}
        present_set = set(clause_data["present_in"])
        for group_name, filenames in grouped.items():
            present_in_group = [f for f in filenames if f in present_set]
            pct = round(len(present_in_group)/len(filenames)*100, 1) if filenames else 0
            comparison[clause_name][group_name] = {"present": len(present_in_group), "total": len(filenames), "percentage": pct, "files": present_in_group}
    divergences = []
    for clause_name, group_data in comparison.items():
        pcts = {g: group_data[g]["percentage"] for g in group_data}
        if len(pcts) >= 2:
            max_pct, min_pct = max(pcts.values()), min(pcts.values())
            if max_pct - min_pct >= 30:
                divergences.append({"clause": clause_name, "max_group": max(pcts, key=pcts.get), "max_pct": max_pct, "min_group": min(pcts, key=pcts.get), "min_pct": min_pct, "gap": round(max_pct-min_pct, 1)})
    return {"assignments": assignments, "grouped": grouped, "comparison": comparison, "divergences": sorted(divergences, key=lambda x: x["gap"], reverse=True)}
