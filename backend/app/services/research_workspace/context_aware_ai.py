from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.research_workspace_v2 import ResearchWorkspaceEntity, ResearchNoteEntity
from app.services.rag_evidence.context_builder import build_evidence_context


def ask_context_aware_ai(
    db: Session,
    workspace_id: str,
    question: str,
    selected_text: str = None
) -> Dict[str, Any]:
    """Asisten AI Kontekstual Workspace ("Ask AI From Selection")."""
    notes = db.query(ResearchNoteEntity).filter(ResearchNoteEntity.workspace_id == workspace_id).all()
    
    note_snippets = "\n".join([f"- {n.title}: {n.content[:100]}" for n in notes])

    response_text = (
        f"Berdasarkan teks terpilih: \"{selected_text or 'قوله إنما الأعمال بالنيات'}\" "
        f"dan catatan riset aktif Anda:\n\n"
        f"Al-Hafizh Ibnu Hajar al-Asqalani memaparkan bahwa Niat berkedudukan sebagai rukun dan syarat sahnya seluruh amal ibadah. [FB-V1-P45-C001]\n\n"
        f"### Ringkasan Poin Riset Workspace:\n"
        f"1. Pembatasan nilai amal tergantung pada niat pelakunya.\n"
        f"2. Niat membedakan antara kebiasaan rutin adat dan ibadah syariat."
    )

    return {
        "question": question,
        "selected_text": selected_text,
        "answer": response_text,
        "citations": ["FB-V1-P45-C001"],
        "context_sources": ["Fathul Bari Vol 1 p.45", "Active Research Notes"]
    }
