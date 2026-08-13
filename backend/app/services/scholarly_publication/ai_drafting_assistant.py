from typing import Dict, Any


def generate_ai_draft_paragraph(prompt: str, context_text: str = None) -> Dict[str, Any]:
    """Asisten Penyusun Draf AI Terkontrol dengan Penandaan Asal Content (HUMAN vs AI_DRAFT)."""
    draft_text = (
        "Berdasarkan analisis Fathul Bari Jilid 1 Halaman 45, Al-Hafizh Ibnu Hajar al-Asqalani memaparkan "
        "bahwa niat berfungsi membedakan antara ibadah syariat dan kebiasaan rutin adat. [FB-V1-P45-C001]"
    )
    return {
        "id": "b-ai-draft-new",
        "type": "PARAGRAPH",
        "text": draft_text,
        "origin": "AI_DRAFT",
        "review_status": "UNREVIEWED",
        "citation_id": "FB-V1-P45-C001"
    }
