import hashlib
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def compute_file_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def extract_pdf(
    pdf_path: str,
    output_dir: str = "data/fathul_bari/extracted",
) -> list[dict[str, Any]]:
    """Mengekstrak teks halaman per halaman dari file PDF Fathul Bari."""
    pdf = Path(pdf_path)
    if not pdf.exists():
        raise FileNotFoundError(f"File PDF tidak ditemukan: {pdf_path}")

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    file_hash = compute_file_hash(pdf)
    pages: list[dict[str, Any]] = []

    try:
        import pdfplumber

        with pdfplumber.open(pdf) as doc:
            total_pages = len(doc.pages)
            logger.info("Mulai ekstraksi %d halaman dari %s...", total_pages, pdf.name)

            for page_number, page in enumerate(doc.pages, start=1):
                text = page.extract_text(x_tolerance=2, y_tolerance=3) or ""
                record = {
                    "pdf_page": page_number,
                    "printed_page": page_number,  # Dapat disesuaikan dengan header/footer offset
                    "text": text,
                    "source_file": str(pdf),
                    "source_hash": file_hash,
                }
                pages.append(record)

                page_file = out_path / f"page_{page_number:04d}.txt"
                page_file.write_text(text, encoding="utf-8")

    except ImportError:
        logger.warning("pdfplumber tidak terpasang, mencoba pypdf fallback...")
        import pypdf

        reader = pypdf.PdfReader(str(pdf))
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            record = {
                "pdf_page": page_number,
                "printed_page": page_number,
                "text": text,
                "source_file": str(pdf),
                "source_hash": file_hash,
            }
            pages.append(record)

            page_file = out_path / f"page_{page_number:04d}.txt"
            page_file.write_text(text, encoding="utf-8")

    logger.info("Selesai mengekstrak %d halaman ke %s", len(pages), str(out_path))
    return pages
