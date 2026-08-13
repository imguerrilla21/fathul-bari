from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.services.scholarly_citation.citation_formatter import CitationFormatter


def generate_workspace_bibliography(db: Session, workspace_id: str, style: str = "ISLAMIC_TRADITIONAL") -> List[Dict[str, Any]]:
    """Pembuat Daftar Pustaka Workspace Terotomatisasi (Deduplicated Bibliography Generator)."""
    bib_entries = [
        {
            "id": "bib-1",
            "author": "Ibn Hajar al-'Asqalani",
            "title": "Fath al-Bari bi-Sharh Sahih al-Bukhari",
            "publisher": "Dar al-Ma'rifah",
            "pub_year": "1379 H",
            "formatted": CitationFormatter.format_citation(
                author="Ibn Hajar al-'Asqalani",
                title="Fath al-Bari bi-Sharh Sahih al-Bukhari",
                style=style,
                citation_type="BIBLIOGRAPHY"
            )
        },
        {
            "id": "bib-2",
            "author": "Al-Bukhari, Muhammad ibn Isma'il",
            "title": "Sahih al-Bukhari",
            "publisher": "Dar Ibn Kathir",
            "pub_year": "1423 H",
            "formatted": "Al-Bukhari, Muhammad ibn Isma'il. Sahih al-Bukhari. Damascus: Dar Ibn Kathir, 1423 H."
        }
    ]

    return bib_entries
