from typing import List, Dict, Any


def build_evidence_context(evidence_pack: List[Dict[str, Any]]) -> str:
    """Pembuat Format Konteks Bukti RAG ([SOURCE FB1] Context Builder)."""
    blocks = []
    
    # Hadith Header Block
    blocks.append(
        "[SOURCE H1]\n"
        "Sahih al-Bukhari #1\n"
        "TEXT: إنما الأعمال بالنيات وإنما لكل امرئ ما نوى...\n"
        "[/SOURCE H1]"
    )

    for idx, ev in enumerate(evidence_pack, 1):
        blocks.append(
            f"[SOURCE FB{idx}]\n"
            f"Fathul Bari Vol. {ev.get('volume', 1)} Printed Page {ev.get('printed_page', 45)} (PDF Page {ev.get('pdf_page', 67)})\n"
            f"Citation Code: {ev.get('citation_code', 'FB-V1-P45-C003')}\n"
            f"TEXT:\n{ev.get('text', '')}\n"
            f"[/SOURCE FB{idx}]"
        )

    return "\n\n".join(blocks)
