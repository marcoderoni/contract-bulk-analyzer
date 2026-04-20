# Copyright (c) 2026 Marco De Roni. All rights reserved.
# Licensed under the MIT License — see LICENSE file for details.

import streamlit as st
import os
import tempfile
import yaml
from analyzer.extractor import load_contracts
from analyzer.keyword_scan import scan_keywords
from analyzer.clause_scan import scan_clauses
from analyzer.metadata_scan import scan_metadata
from analyzer.comparator import compare_groups
from analyzer.reporter import generate_excel, generate_word

st.set_page_config(
    page_title="Contract Bulk Analyzer",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Contract Bulk Analyzer")
st.caption("Cross-portfolio contract analysis — keyword frequency, clause presence, metadata extraction and group comparison")

# ── Sidebar ──
with st.sidebar:
    st.header("⚙️ Configuration")

    # Upload queries YAML
    queries_file = st.file_uploader("Upload queries.yaml", type=["yaml", "yml"])
    if queries_file:
        queries = yaml.safe_load(queries_file)
        st.success(f"✅ Queries loaded: {len(queries.get('keywords', []))} keywords, {len(queries.get('clauses', []))} clauses")
    else:
        # Load default
        default_path = "config/queries.yaml"
        if os.path.exists(default_path):
            with open(default_path) as f:
                queries = yaml.safe_load(f)
            st.info("Using default config/queries.yaml")
        else:
            queries = None
            st.warning("No queries file found")

    # One-off keyword
    extra_keyword = st.text_input("Add one-off keyword", placeholder="e.g. force majeure")

    # PII sanitization toggle
    sanitize_pii = st.checkbox("🔒 Enable PII sanitization", value=True)

# ── Main ──
uploaded_files = st.file_uploader(
    "Upload contracts (PDF or DOCX)",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

if uploaded_files and queries:
    if st.button("▶ Run Analysis", type="primary"):

        with st.spinner("Analysing contracts..."):

            # Save uploaded files to temp directory
            with tempfile.TemporaryDirectory() as tmpdir:
                for uploaded_file in uploaded_files:
                    path = os.path.join(tmpdir, uploaded_file.name)
                    with open(path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                # Load contracts
                contracts = load_contracts(tmpdir)

                # PII sanitization
                pii_mappings = {}
                if sanitize_pii:
                    try:
                        from analyzer.sanitizer import sanitize
                        sanitized = {}
                        for filename, text in contracts.items():
                            s_text, mapping = sanitize(text)
                            sanitized[filename] = s_text
                            pii_mappings[filename] = mapping
                        contracts = sanitized
                        total_pii = sum(len(m) for m in pii_mappings.values())
                        st.info(f"🔒 PII sanitized: {total_pii} entities redacted across {len(contracts)} contracts")
                    except Exception as e:
                        st.warning(f"PII sanitization skipped: {e}")

                # Add one-off keyword
                keywords = list(queries.get("keywords", []))
                if extra_keyword:
                    keywords.append(extra_keyword)

                clauses = queries.get("clauses", [])
                meta_config = queries.get("metadata", {})
                groups_config = queries.get("comparison_groups", [])

                # Run analysis
                keyword_results = scan_keywords(contracts, keywords)
                clause_results = scan_clauses(contracts, clauses)
                metadata_results = scan_metadata(contracts, meta_config)
                comparison_results = {}
                if groups_config and len(contracts) > 1:
                    comparison_results = compare_groups(contracts, clause_results, groups_config)

                # Build PII summary
                pii_summary = {
                    "total_entities": sum(len(m) for m in pii_mappings.values()),
                    "contracts_count": len(pii_mappings),
                    "breakdown": {}
                }
                for mapping in pii_mappings.values():
                    for placeholder in mapping.keys():
                        entity_type = placeholder.split("_")[0].replace("[", "")
                        pii_summary["breakdown"][entity_type] = pii_summary["breakdown"].get(entity_type, 0) + 1

        # ── Results ──
        st.success(f"✅ Analysis complete — {len(contracts)} contracts analysed")

        tab1, tab2, tab3, tab4 = st.tabs(["🔍 Keywords", "📋 Clauses", "📊 Metadata", "🔀 Groups"])

        with tab1:
            st.subheader("Keyword Frequency")
            import pandas as pd
            kw_data = []
            for kw, data in keyword_results.items():
                kw_data.append({
                    "Keyword": kw,
                    "Found In": data["contracts_found"],
                    "Total": data["contracts_total"],
                    "% Presence": data["percentage"],
                    "Confidence": data.get("confidence", "")
                })
            st.dataframe(pd.DataFrame(kw_data), use_container_width=True)

        with tab2:
            st.subheader("Clause Presence")
            cl_data = []
            for name, data in clause_results.items():
                cl_data.append({
                    "Clause": name,
                    "Present": data["present_count"],
                    "Absent": data["absent_count"],
                    "% Presence": data["presence_pct"],
                    "Missing In": ", ".join(data["absent_in"]) if data["absent_in"] else "—"
                })
            st.dataframe(pd.DataFrame(cl_data), use_container_width=True)

        with tab3:
            st.subheader("Metadata Extraction")
            meta_data = []
            for filename, meta in metadata_results.items():
                meta_data.append({
                    "Contract": filename,
                    "Parties": meta.get("parties", "—"),
                    "Effective Date": meta.get("effective_date", "—"),
                    "Governing Law": meta.get("governing_law", "—"),
                    "Notice Period": meta.get("notice_period", "—"),
                    "Auto-Renewal": meta.get("auto_renewal", "—"),
                })
            st.dataframe(pd.DataFrame(meta_data), use_container_width=True)

        with tab4:
            st.subheader("Group Comparison")
            if comparison_results and comparison_results.get("divergences"):
                divergences = comparison_results["divergences"]
                st.warning(f"⚠️ {len(divergences)} significant divergences found:")
                for d in divergences:
                    st.write(f"**{d['clause']}**: {d['max_group']} {d['max_pct']}% vs {d['min_group']} {d['min_pct']}% (gap: {d['gap']}%)")
            else:
                st.info("No significant divergences found between groups.")

        # ── Download ──
        st.subheader("📥 Download Reports")
        output_dir = tempfile.mkdtemp()

        excel_path = generate_excel(keyword_results, clause_results, metadata_results, comparison_results, output_dir)
        word_path = generate_word(keyword_results, clause_results, metadata_results, comparison_results, output_dir, pii_summary=pii_summary)

        col1, col2 = st.columns(2)
        with col1:
            with open(excel_path, "rb") as f:
                st.download_button("📊 Download Excel", f, file_name="bulk_analysis.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col2:
            with open(word_path, "rb") as f:
                st.download_button("📝 Download Word", f, file_name="bulk_report.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

elif not queries:
    st.warning("⚠️ Please upload a queries.yaml file or ensure config/queries.yaml exists.")
else:
    st.info("👆 Upload one or more contracts to begin analysis.")