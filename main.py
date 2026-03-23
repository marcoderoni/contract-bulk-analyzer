# Copyright (c) 2025 Marco De Roni. All rights reserved.
# Licensed under the MIT License — see LICENSE file for details.

import os
import sys
import yaml
from colorama import Fore, Style, init
from tqdm import tqdm
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


def load_queries() -> dict:
    if not os.path.exists(QUERIES_PATH):
        print(Fore.RED + f"\n❌ File queries non trovato: {QUERIES_PATH}")
        print(Fore.YELLOW + "   Copia config/queries.example.yaml → config/queries.yaml")
        sys.exit(1)
    with open(QUERIES_PATH) as f:
        content = yaml.safe_load(f)
    if not content or not isinstance(content, dict):
        print(Fore.RED + f"\n❌ File queries vuoto o non valido: {QUERIES_PATH}")
        sys.exit(1)
    return content


def main():
    print(Fore.WHITE + Style.BRIGHT + "\n=== Contract Bulk Analyzer ===\n")

    # 1. Carica queries
    queries = load_queries()
    keywords = queries.get("keywords", [])
    clauses = queries.get("clauses", [])
    meta_config = queries.get("metadata", {})
    groups_config = queries.get("comparison_groups", [])

    # 2. Carica contratti
    print(Fore.CYAN + "📂 Caricamento contratti...")
    contracts = load_contracts(CONTRACTS_DIR)

    if not contracts:
        print(Fore.YELLOW + f"\n⚠️  Nessun contratto trovato in '{CONTRACTS_DIR}/'")
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

    # 7. Genera report
    print(Fore.CYAN + "\n📝 Generazione report...")
    excel_path = generate_excel(
        keyword_results, clause_results,
        metadata_results, comparison_results, OUTPUT_DIR
    )
    word_path = generate_word(
        keyword_results, clause_results,
        metadata_results, comparison_results, OUTPUT_DIR
    )

    print(Fore.WHITE + Style.BRIGHT + "\n" + "="*60)
    print(Fore.GREEN + f"✅ Analisi completata!")
    print(f"   📊 Excel: {excel_path}")
    print(f"   📝 Word:  {word_path}")
    print("="*60)


if __name__ == "__main__":
    main()