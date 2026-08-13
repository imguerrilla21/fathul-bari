import json
import uuid
from sqlalchemy import select

from app.database import SessionLocal
from app.models.hadith import Hadith
from app.models.sharh import SharhSection
from app.models.workspace import (
    ResearchAnnotation,
    ResearchCitation,
    ResearchNote,
    ResearchProject,
)


def seed_workspace():
    db = SessionLocal()
    try:
        # Cek apakah sudah ada project
        existing = db.scalar(select(ResearchProject).where(ResearchProject.title.like("%Niat%")))
        if existing:
            print(f"[i] Proyek sample sudah ada: {existing.title}")
            return existing.id

        h1 = db.scalar(select(Hadith).where(Hadith.external_number == 1))
        h2 = db.scalar(select(Hadith).where(Hadith.external_number == 2))

        sec1 = db.scalar(select(SharhSection).where(SharhSection.volume == 1, SharhSection.printed_page == 9))
        sec2 = db.scalar(select(SharhSection).where(SharhSection.volume == 1, SharhSection.printed_page == 24))

        proj = ResearchProject(
            id=uuid.uuid4(),
            title="Kajian Tematik Niat & Permulaan Turunnya Wahyu dalam Syarah Fathul Bari",
            description="Penelitian mendalam mengenai korelasi niat, permulaan kenabian, dan metodologi pensyarahan Al-Hafizh Ibnu Hajar al-Asqalani pada Shahih al-Bukhari.",
            created_by="Dr. Ahmad Sanusi (Muhaqqiq Peneliti)",
            status="active",
        )
        db.add(proj)
        db.flush()

        # Notes
        n1 = ResearchNote(
            id=uuid.uuid4(),
            project_id=proj.id,
            content="### Pondasi Keikhlasan Niat (Hadis #1)\nImam Al-Bukhari menempatkan hadis niat di awal kitab sebagai pengingat utama (*tanbih*) bahwa segala amal ibadah dan penulisan ilmu harus diawali dengan keikhlasan semata karena Allah SWT.",
            hadith_id=h1.id if h1 else None,
            sharh_section_id=sec1.id if sec1 else None,
            source_page_id="vol_1_p_9",
            tags_json=json.dumps(["niat", "ushul_hadits", "keikhlasan"]),
        )
        n2 = ResearchNote(
            id=uuid.uuid4(),
            project_id=proj.id,
            content="### Peristiwa Turunnya Wahyu Seperti Lonceng (Hadis #2)\nIbnu Hajar menguraikan bahwa bunyi 'gemerincing lonceng' (*salsalatul jaras*) mengindikasikan beratnya kondisi saat wahyu pertama kali diterima, di mana keringat mengalir deras dari kening Rasulullah SAW bahkan di hari yang sangat dingin.",
            hadith_id=h2.id if h2 else None,
            sharh_section_id=sec2.id if sec2 else None,
            source_page_id="vol_1_p_24",
            tags_json=json.dumps(["wahyu", "salsalah", "kenabian"]),
        )
        db.add_all([n1, n2])

        # Annotations
        a1 = ResearchAnnotation(
            id=uuid.uuid4(),
            project_id=proj.id,
            hadith_id=h1.id if h1 else None,
            sharh_section_id=sec1.id if sec1 else None,
            selected_text="إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى",
            annotation_type="IMPORTANT",
            comment="Kaidah fiqih universal: Niat membedakan antara adat kebiasaan dengan ibadah, serta menentukan sah dan bernilainya suatu perbuatan di sisi Allah.",
        )
        a2 = ResearchAnnotation(
            id=uuid.uuid4(),
            project_id=proj.id,
            hadith_id=h2.id if h2 else None,
            sharh_section_id=sec2.id if sec2 else None,
            selected_text="أَحْيَانًا يَأْتِينِي مِثْلَ صَلْصَلَةِ الْجَرَسِ وَهُوَ أَشَدُّهُ عَلَيَّ",
            annotation_type="NOTE",
            comment="Ibnu Hajar menerangkan bahwa perumpamaan dengan lonceng adalah pada aspek suara yang kuat, jelas, dan menghentak kesadaran indera batin.",
        )
        db.add_all([a1, a2])

        # Citations
        c1 = ResearchCitation(
            id=uuid.uuid4(),
            project_id=proj.id,
            hadith_id=h1.id if h1 else None,
            sharh_section_id=sec1.id if sec1 else None,
            citation_text="[Fathul Bari, Jilid 1, Hlm. 9, Edisi Dar al-Ma'rifah]",
            work_title="Fathul Bari Syarah Shahih al-Bukhari",
            author="Al-Hafizh Ibnu Hajar al-Asqalani",
            edition="Dar al-Ma'rifah, Beirut",
            volume=1,
            printed_page=9,
            pdf_page=9,
            source_file="fb001.pdf",
        )
        c2 = ResearchCitation(
            id=uuid.uuid4(),
            project_id=proj.id,
            hadith_id=h2.id if h2 else None,
            sharh_section_id=sec2.id if sec2 else None,
            citation_text="[Fathul Bari, Jilid 1, Hlm. 24, Edisi Dar al-Ma'rifah]",
            work_title="Fathul Bari Syarah Shahih al-Bukhari",
            author="Al-Hafizh Ibnu Hajar al-Asqalani",
            edition="Dar al-Ma'rifah, Beirut",
            volume=1,
            printed_page=24,
            pdf_page=24,
            source_file="fb001.pdf",
        )
        db.add_all([c1, c2])

        db.commit()
        print(f"[✓] Berhasil membuat sample proyek riset: '{proj.title}'")
        return proj.id
    finally:
        db.close()


if __name__ == "__main__":
    seed_workspace()
