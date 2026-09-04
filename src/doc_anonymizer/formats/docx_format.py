"""Anonymisation de fichiers .docx (paragraphes et tableaux).

Limitation connue : un paragraphe est anonymisé comme un bloc de texte
unique puis réinjecté dans son premier "run" ; la mise en forme différenciée
entre plusieurs runs d'un même paragraphe (ex: un mot en gras au milieu
d'une phrase) n'est donc pas préservée si ce mot est remplacé. Les
en-têtes, pieds de page et zones de texte ne sont pas traités.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from ..anonymizer import Anonymizer


def _anonymize_paragraph(paragraph: Paragraph, anonymizer: Anonymizer) -> int:
    original = paragraph.text
    if not original:
        return 0

    result = anonymizer.anonymize_text(original)
    if result.text == original:
        return 0

    if paragraph.runs:
        paragraph.runs[0].text = result.text
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(result.text)

    return len(result.matches)


def _iter_tables(tables: Iterable[Table]):
    for table in tables:
        yield table
        for row in table.rows:
            for cell in row.cells:
                yield from _iter_tables(cell.tables)


def anonymize_docx(input_path: Path, output_path: Path, anonymizer: Anonymizer) -> int:
    document = Document(str(input_path))
    total_matches = 0

    for paragraph in document.paragraphs:
        total_matches += _anonymize_paragraph(paragraph, anonymizer)

    for table in _iter_tables(document.tables):
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    total_matches += _anonymize_paragraph(paragraph, anonymizer)

    document.save(str(output_path))
    return total_matches
