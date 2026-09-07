from .txt import anonymize_txt
from .csv_format import anonymize_csv
from .docx_format import anonymize_docx
from .pdf_format import anonymize_pdf

__all__ = ["anonymize_txt", "anonymize_csv", "anonymize_docx", "anonymize_pdf"]

HANDLERS = {
    ".txt": anonymize_txt,
    ".md": anonymize_txt,
    ".csv": anonymize_csv,
    ".docx": anonymize_docx,
    ".pdf": anonymize_pdf,
}
