import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.research_workspace_v2 import ResearchWorkspaceEntity, ResearchNoteEntity, ResearchFindingEntity

logger = logging.getLogger("workspace_service")


def create_workspace_with_defaults(db: Session, name: str = "Ruang Kerja Hadis Niat", description: str = "Penelitian Syarah Hadis Niat Fathul Bari") -> ResearchWorkspaceEntity:
    """Membuat ruang kerja riset baru beserta catatan awal & temuan awal."""
    ws = db.query(ResearchWorkspaceEntity).filter(ResearchWorkspaceEntity.name == name).first()
    if not ws:
        ws = ResearchWorkspaceEntity(
            name=name,
            description=description,
            status="ACTIVE",
            metadata_json={
                "panels": {"hadith": 30, "source": 45, "notes": 25},
                "active_tab": "notes"
            }
        )
        db.add(ws)
        db.commit()
        db.refresh(ws)

        # Seed initial research note
        note = ResearchNoteEntity(
            workspace_id=ws.id,
            title="Catatan Awal: Makna Niat & Keikhlasan",
            content=(
                "## Analisis Niat dalam Syarah Fathul Bari\n\n"
                "Ibnu Hajar al-Asqalani menekankan bahwa niat merupakan rukun utama dalam setiap amal ibadah. "
                "Sitasi pendukung: [FB-V1-P45-C001].\n\n"
                "### Poin Penting:\n"
                "1. Niat membedakan ibadah dari kebiasaan rutin.\n"
                "2. Niat membedakan tingkatan ibadah (wajib vs sunnah)."
            ),
            content_format="markdown",
            note_type="OBSERVATION"
        )
        db.add(note)

        # Seed initial research finding
        finding = ResearchFindingEntity(
            workspace_id=ws.id,
            title="Temuan: Syarat Sah Ibadah Adalah Niat",
            statement="Al-Hafizh Ibnu Hajar menegaskan kesepakatan ulama bahwa niat adalah syarat sahnya seluruh ibadah dalam Fathul Bari.",
            status="SUPPORTED",
            confidence=0.98
        )
        db.add(finding)
        db.commit()

    return ws
