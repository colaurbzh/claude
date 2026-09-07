from __future__ import annotations

from pathlib import Path

from ..anonymizer import Anonymizer


def anonymize_txt(input_path: Path, output_path: Path, anonymizer: Anonymizer) -> int:
    text = input_path.read_text(encoding="utf-8")
    result = anonymizer.anonymize_text(text)
    output_path.write_text(result.text, encoding="utf-8")
    return len(result.matches)
