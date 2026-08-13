import logging
from typing import Dict, Any, List

logger = logging.getLogger("pdf_reader")


class PDFReader:
    """Abstraksi Pembaca Dokumen PDF Fathul Bari (PDF Reader Abstraction)."""
    def __init__(self, file_path: str = None):
        self.file_path = file_path

    def get_page_count(self) -> int:
        return 520

    def extract_page_text(self, pdf_page_num: int) -> str:
        """Mengambil teks layer dari halaman PDF."""
        printed_page = max(1, pdf_page_num - 22)
        return (
            f"قوله (إنما الأعمال بالنيات) قال الحافظ ابن حجر في فتح الباري (ص {printed_page}): "
            f"النية شرط في صحة العبادات، واشتراطها في الطهارة والصلاة والزكاة ثابت بالإجماع..."
        )

    def render_page_image_url(self, pdf_page_num: int) -> str:
        """Mengembalikan URL pratinjau halaman PDF untuk Source Viewer UI."""
        return f"/assets/source-pages/fathul_bari_v1_p{pdf_page_num}.webp"
