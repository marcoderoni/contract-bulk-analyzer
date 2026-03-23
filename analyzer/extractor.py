# Copyright (c) 2025 Marco De Roni. All rights reserved.
import pdfplumber, docx, os, re

def extract_text_from_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t: text += t + "\n"
    return text

def extract_text_from_docx(path):
    doc = docx.Document(path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def extract_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf": return extract_text_from_pdf(path)
    elif ext == ".docx": return extract_text_from_docx(path)
    raise ValueError(f"Formato non supportato: {ext}")

def load_contracts(contracts_dir):
    contracts = {}
    files = [f for f in os.listdir(contracts_dir) if f.lower().endswith((".pdf",".docx"))]
    for filename in sorted(files):
        path = os.path.join(contracts_dir, filename)
        try:
            text = extract_text(path)
            if text.strip(): contracts[filename] = text
        except Exception as e:
            print(f"   Errore su {filename}: {e}")
    return contracts
