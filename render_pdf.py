#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rend le HTML du rapport en PDF avec WeasyPrint.

Usage : python3 render_pdf.py [source.html] [destination.pdf]
Les chemins relatifs des images sont résolus depuis le dossier du HTML.
"""
from pathlib import Path
import sys
from weasyprint import HTML
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
source = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE / "Dossier_projet_gestion_administrative_scolaire_FINAL.html"
destination = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else HERE / "Dossier_projet_gestion_administrative_scolaire_FINAL.pdf"

if not source.is_file():
    raise SystemExit(f"HTML source introuvable : {source}")

HTML(filename=str(source), base_url=str(source.parent)).write_pdf(str(destination))
reader = PdfReader(str(destination))
if len(reader.pages) < 10:
    raise SystemExit(f"PDF incomplet : seulement {len(reader.pages)} pages")
print(f"PDF généré : {destination} ({len(reader.pages)} pages)")
