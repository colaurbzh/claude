import csv
from pathlib import Path

from doc_anonymizer.anonymizer import Anonymizer
from doc_anonymizer.formats import anonymize_csv, anonymize_docx, anonymize_txt


def test_anonymize_txt(tmp_path: Path):
    src = tmp_path / "in.txt"
    src.write_text("Email : jean@exemple.fr", encoding="utf-8")
    dst = tmp_path / "out.txt"

    anonymizer = Anonymizer(entity_types=["email"])
    count = anonymize_txt(src, dst, anonymizer)

    assert count == 1
    assert "jean@exemple.fr" not in dst.read_text(encoding="utf-8")


def test_anonymize_csv(tmp_path: Path):
    src = tmp_path / "in.csv"
    with src.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["nom", "email"])
        writer.writerow(["Jean", "jean@exemple.fr"])
    dst = tmp_path / "out.csv"

    anonymizer = Anonymizer(entity_types=["email"])
    count = anonymize_csv(src, dst, anonymizer)

    assert count == 1
    rows = list(csv.reader(dst.open(encoding="utf-8")))
    assert rows[1][1] == "[EMAIL_1]"


def test_anonymize_docx(tmp_path: Path):
    docx = __import__("docx")
    src = tmp_path / "in.docx"
    document = docx.Document()
    document.add_paragraph("Contact : jean@exemple.fr")
    table = document.add_table(rows=1, cols=1)
    table.rows[0].cells[0].text = "tel: 06 12 34 56 78"
    document.save(str(src))

    dst = tmp_path / "out.docx"
    anonymizer = Anonymizer(entity_types=["email", "phone"])
    count = anonymize_docx(src, dst, anonymizer)

    assert count == 2
    result_doc = docx.Document(str(dst))
    full_text = "\n".join(p.text for p in result_doc.paragraphs)
    assert "jean@exemple.fr" not in full_text
    assert result_doc.tables[0].rows[0].cells[0].text == "tel: [TELEPHONE_1]"
