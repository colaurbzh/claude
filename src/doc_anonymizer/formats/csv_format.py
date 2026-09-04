from __future__ import annotations

import csv
from pathlib import Path

from ..anonymizer import Anonymizer


def _sniff_dialect(sample: str) -> csv.Dialect:
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        return csv.excel


def anonymize_csv(input_path: Path, output_path: Path, anonymizer: Anonymizer) -> int:
    raw = input_path.read_text(encoding="utf-8")
    dialect = _sniff_dialect(raw[:4096])

    rows = list(csv.reader(raw.splitlines(), dialect=dialect))
    total_matches = 0
    anonymized_rows = []
    for row in rows:
        new_row = []
        for cell in row:
            result = anonymizer.anonymize_text(cell)
            total_matches += len(result.matches)
            new_row.append(result.text)
        anonymized_rows.append(new_row)

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, dialect=dialect)
        writer.writerows(anonymized_rows)

    return total_matches
