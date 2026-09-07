"""Anonymisation de fichiers PDF.

Deux modes selon les dépendances disponibles :

- Si PyMuPDF (`pymupdf`, module `fitz`) est installé : véritable caviardage
  (le texte original est effacé de la page, pas seulement masqué
  visuellement) via les annotations de rédaction natives du PDF.
- Sinon : repli sur une extraction de texte (pypdf) suivie d'une
  anonymisation, écrite dans un fichier .txt à côté de la sortie demandée,
  car reconstruire un PDF fidèle sans PyMuPDF n'est pas fiable.

Limite connue même avec PyMuPDF : une correspondance qui s'étend sur
plusieurs lignes (ex : une adresse postale sur deux lignes) peut ne pas être
localisée visuellement par `search_for`, même si elle a été détectée dans le
texte extrait. Les PDF scannés (image sans couche texte) ne sont pas gérés :
utiliser un OCR en amont.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ..anonymizer import Anonymizer

logger = logging.getLogger("doc_anonymizer")


def anonymize_pdf(input_path: Path, output_path: Path, anonymizer: Anonymizer) -> int:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return _anonymize_pdf_fallback(input_path, output_path, anonymizer)
    return _anonymize_pdf_with_redaction(input_path, output_path, anonymizer, fitz)


def _anonymize_pdf_with_redaction(input_path: Path, output_path: Path, anonymizer: Anonymizer, fitz) -> int:
    doc = fitz.open(str(input_path))
    total_matches = 0

    for page in doc:
        text = page.get_text()
        if not text:
            continue
        result = anonymizer.anonymize_text(text)
        if not result.matches:
            continue

        mapping = anonymizer.mapping
        for m in result.matches:
            replacement = mapping.get(f"{m.entity_type}::{m.text}", f"[{m.entity_type}]")
            areas = page.search_for(m.text)
            for area in areas:
                page.add_redact_annot(area, text=replacement, fill=(0, 0, 0), text_color=(1, 1, 1))
            total_matches += 1 if areas else 0
            if not areas:
                logger.warning(
                    "Correspondance détectée mais non localisée visuellement (probablement sur "
                    "plusieurs lignes) : %s", m.entity_type,
                )
        page.apply_redactions()

    doc.save(str(output_path))
    doc.close()
    return total_matches


def _anonymize_pdf_fallback(input_path: Path, output_path: Path, anonymizer: Anonymizer) -> int:
    from pypdf import PdfReader

    reader = PdfReader(str(input_path))
    full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    result = anonymizer.anonymize_text(full_text)

    txt_output = output_path.with_suffix(".txt")
    txt_output.write_text(result.text, encoding="utf-8")

    logger.warning(
        "PyMuPDF n'est pas installé : impossible de produire un PDF caviardé. "
        "Le texte extrait et anonymisé a été écrit dans %s à la place. "
        "Installez le PDF avec `pip install doc-anonymizer[pdf-redact]` pour un vrai caviardage.",
        txt_output,
    )
    return len(result.matches)
