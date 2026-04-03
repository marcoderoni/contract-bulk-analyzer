# Copyright (c) 2026 Marco De Roni. All rights reserved.
# Licensed under the MIT License — see LICENSE file for details.

import os
import sys
import argparse
import yaml
from colorama import Fore, Style, init
from analyzer.extractor import load_contracts
from analyzer.keyword_scan import scan_keywords
from analyzer.clause_scan import scan_clauses
from analyzer.metadata_scan import scan_metadata
from analyzer.comparator import compare_groups
from analyzer.reporter import generate_excel, generate_word

init(autoreset=True)

QUERIES_PATH = "config/queries.yaml"
CONTRACTS_DIR = "contracts"
OUTPUT_DIR = "output"


def parse_args():
    parser = argparse.ArgumentParser(description="Contract Bulk Analyzer — cross-contract analysis")
    parser.add_argument("--queries", type=str, help="Path to queries YAML file")
    parser.add_argument("--contracts", type=str, help="Path to contracts folder")
    parser.add_argument("--output", type=str, help="Path to output folder")
    parser.add_argument("--keyword", type=str, help="Add a one-off keyword to search")
    return parser.parse_args()


def load_queries(path: str) -> dict:
    if not os.path.exists(path):
        print(Fore.RED + f"\n❌ File queries non trovato: {path}")
        print(Fore.YELLOW + "   Copia config/queries.example.yaml → config/queries.yaml")
        sys.exit(1)
    with open(path) as f:
        content = yaml.safe_load(f)
    if not content or not isinstance(content, dict):
        print(Fore.RED + f"\n❌ File queries vuoto o non valido: {path}")
        sys.exit(1)
    return content


def main():
    args = parse_args()

    queries_path = args.queries or QUERIES_PATH
    contracts_dir = args.contracts or CONTRACTS_DIR
    output_dir = args.output or OUTPUT_DIR

    print(Fore.WHITE + Style.BRIGHT + "\n=== Contract Bulk Analyzer ===\n")

    # 1. Carica queries
    queries = load_queries(queries_path)
    keywords = queries.get("keywords", [])
    clauses = queries.get("clauses", [])
    meta_config = queries.get("metadata", {})
    groups_config = queries.get("comparison_groups", [])

    # Add one-off keyword from CLI
    if args.keyword:
        keywords = list(keywords) + [args.keyword]
        print(Fore.CYAN + f"   + Keyword aggiunta: {args.keyword}\n")

    # 2. Carica contratti
    print(Fore.CYAN + "📂 Caricamento contratti...")
    contracts = load_contracts(contracts_dir)

    # Sanitize PII
    pii_mappings = {}
    sanitized_contracts = {}
    try:
        from analyzer.sanitizer import sanitize
        for filename, text in contracts.items():
            sanitized_text, mapping = sanitize(text)
            sanitized_contracts[filename] = sanitized_text
            pii_mappings[filename] = mapping
        total_entities = sum(len(m) for m in pii_mappings.values())
        print(Fore.GREEN + f"   ✓ PII sanitizzato: {total_entities} entità redatte in {len(contracts)} contratti")
        contracts = sanitized_contracts
    except Exception as e:
        print(Fore.YELLOW + f"   ⚠️  PII sanitization skipped: {e}")

    if not contracts:
        print(Fore.YELLOW + f"\n⚠️  Nessun contratto trovato in '{contracts_dir}/'")
        print("   Metti uno o più file PDF o DOCX nella cartella contracts/ e riprova.")
        return

    print(Fore.GREEN + f"   ✓ {len(contracts)} contratti caricati\n")

    # 3. Keyword scan
    print(Fore.CYAN + "🔍 Keyword frequency scan...")
    keyword_results = scan_keywords(contracts, keywords)
    for kw, data in keyword_results.items():
        color = Fore.GREEN if data["percentage"] >= 80 else \
                Fore.YELLOW if data["percentage"] >= 40 else Fore.RED
        print(f"   {color}{kw:40} {data['contracts_found']}/{data['contracts_total']} ({data['percentage']}%)")

    # 4. Clause scan
    print(Fore.CYAN + "\n📋 Clause presence scan...")
    clause_results = scan_clauses(contracts, clauses)
    for name, data in clause_results.items():
        color = Fore.GREEN if data["presence_pct"] >= 80 else \
                Fore.YELLOW if data["presence_pct"] >= 40 else Fore.RED
        missing = f" ← missing in: {', '.join(data['absent_in'])}" if data["absent_in"] else ""
        print(f"   {color}{name:40} {data['presence_pct']}%{missing}")

    # 5. Metadata scan
    print(Fore.CYAN + "\n📊 Metadata extraction...")
    metadata_results = scan_metadata(contracts, meta_config)
    print(Fore.GREEN + f"   ✓ Metadati estratti da {len(metadata_results)} contratti")

    # 6. Group comparison
    comparison_results = {}
    if groups_config and len(contracts) > 1:
        print(Fore.CYAN + "\n🔀 Group comparison...")
        comparison_results = compare_groups(contracts, clause_results, groups_config)
        assignments = comparison_results.get("assignments", {})
        for filename, group in assignments.items():
            print(f"   {filename:50} → {group}")
        divergences = comparison_results.get("divergences", [])
        if divergences:
            print(Fore.YELLOW + f"\n   ⚠️  {len(divergences)} divergenze significative trovate:")
            for d in divergences[:5]:
                print(f"   {d['clause']}: {d['max_group']} {d['max_pct']}% vs {d['min_group']} {d['min_pct']}%")

    # 7. Build PII summary
    pii_summary = {
        "total_entities": sum(len(m) for m in pii_mappings.values()),
        "contracts_count": len(pii_mappings),
        "breakdown": {}
    }
    for mapping in pii_mappings.values():
        for placeholder in mapping.keys():
            entity_type = placeholder.split("_")[0].replace("[", "")
            pii_summary["breakdown"][entity_type] = pii_summary["breakdown"].get(entity_type, 0) + 1

    # 8. Genera report
    print(Fore.CYAN + "\n📝 Generazione report...")
    excel_path = generate_excel(
        keyword_results, clause_results,
        metadata_results, comparison_results, output_dir
    )
    word_path = generate_word(
        keyword_results, clause_results,
        metadata_results, comparison_results,
        output_dir, pii_summary=pii_summary
    )

    # 9. Audit log
    try:
        from analyzer.audit import log_analysis
        entry = log_analysis(
            contracts=list(contracts.keys()),
            keyword_results=keyword_results,
            clause_results=clause_results,
        )
        print(Fore.GREEN + f"   📋 Audit log aggiornato: {entry['timestamp']}")
    except Exception as e:
        print(Fore.YELLOW + f"   ⚠️  Audit log skipped: {e}")

    print(Fore.WHITE + Style.BRIGHT + "\n" + "="*60)
    print(Fore.GREEN + f"✅ Analisi completata!")
    print(f"   📊 Excel: {excel_path}")
    print(f"   📝 Word:  {word_path}")
    print("="*60)


if __name__ == "__main__":
    main()