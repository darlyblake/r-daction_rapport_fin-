#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère le HTML, calcule la pagination si les destinations PDF sont lisibles,
puis rend le PDF. Fonctionne dans le dépôt, sans chemins propres à un ancien poste.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
APP_REPO = Path(os.environ.get("SAS_REPO_PATH", HERE.parent / "Syst-me-Administratif-Scolaire")).resolve()
HTML = HERE / "Dossier_projet_gestion_administrative_scolaire_FINAL.html"
PDF = HERE / "Dossier_projet_gestion_administrative_scolaire_FINAL.pdf"
PAGES = HERE / "pages.json"
ENV = os.environ.copy()
ENV.setdefault("SAS_REPO_PATH", str(APP_REPO))

def render():
    subprocess.run([sys.executable, str(HERE / "render_pdf.py"), str(HTML), str(PDF)], check=True, cwd=HERE, env=ENV)

def page_map():
    reader = PdfReader(str(PDF))
    out = {}
    for key, dest in reader.named_destinations.items():
        try:
            out[key.lstrip("/")] = reader.get_destination_page_number(dest) + 1
        except Exception:
            continue
    return out, len(reader.pages)

previous = None
for attempt in range(5):
    args = [sys.executable, str(HERE / "build_dossier.py")]
    if PAGES.is_file():
        args.append(str(PAGES))
    subprocess.run(args, check=True, cwd=HERE, env=ENV)
    render()
    current, page_count = page_map()
    if not current:
        print("Avertissement : le moteur PDF n'a pas exposé de destinations nommées ; le PDF a été rendu, mais la pagination du sommaire n'a pas été recalculée.")
        break
    if current == previous:
        print(f"Pagination stabilisée après {attempt + 1} passe(s), {page_count} pages.")
        break
    previous = current
    PAGES.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
else:
    print("Avertissement : pagination non stabilisée après cinq passes ; le dernier PDF a été conservé.")
