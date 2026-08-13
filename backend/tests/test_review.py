"""Unit tests for Stage 5 Review Dashboard APIs and Citation Generator."""

import pytest
from app.services.citation_generator import generate_citations


def test_citation_generator_formats():
    citations = generate_citations(
        hadith_number=1,
        collection_name="Shahih al-Bukhari",
        volume=1,
        page=9,
        sharh_title="Syarah Hadis Pertama Innamal A'malu bin-Niyyat",
        hadith_arabic_excerpt="إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ",
    )

    assert "standard" in citations
    assert "chicago" in citations
    assert "bibtex" in citations
    assert "markdown" in citations

    assert "Ibnu Hajar al-Asqalani" in citations["standard"]
    assert "Jilid 1, Hal. 9" in citations["standard"]
    assert "Shahih al-Bukhari No. 1" in citations["standard"]

    assert "Al-Asqalani, Ahmad bin Ali bin Hajar" in citations["chicago"]
    assert "@incollection{" in citations["bibtex"]
    assert "> **Sitasi:**" in citations["markdown"]
    assert "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ" in citations["markdown"]


def test_citation_generator_fallback():
    citations = generate_citations(
        hadith_number=None,
        collection_name=None,
        volume=None,
        page=None,
    )

    assert "Jilid -" in citations["standard"]
    assert "Hal. -" in citations["standard"]
    assert "Shahih al-Bukhari No. -" in citations["standard"]
