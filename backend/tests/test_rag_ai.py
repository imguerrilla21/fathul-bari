"""Unit and Integration tests for RAG / Syarah AI Assistant."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Collection, Hadith, HadithSharhLink, SharhSection, Source
from app.services.citation_validator import audit_ai_response_citations, validate_citation_record
from app.services.rag_retriever import extract_hadith_number_from_query, retrieve_rag_context
from app.services.rag_synthesizer import synthesize_rag_response

# In-memory SQLite for fast testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed source and collection
    source = Source(
        name="Ahmad Sanusi Hadits API",
        source_type="api",
        base_url="https://api.ahmadsanusi.com",
    )
    db.add(source)
    db.flush()

    collection = Collection(
        slug="shahih_bukhari",
        name="Shahih al-Bukhari",
        language="id",
        total_expected=7008,
    )
    db.add(collection)
    db.flush()

    # Hadith #1
    h1 = Hadith(
        collection_id=collection.id,
        source_id=source.id,
        external_number=1,
        arabic_text="إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ",
        translation="Semua perbuatan tergantung niatnya...",
        api_endpoint="/v1/hadits/shahih_bukhari/1",
    )
    # Hadith #2
    h2 = Hadith(
        collection_id=collection.id,
        source_id=source.id,
        external_number=2,
        arabic_text="أَحْيَانًا يَأْتِينِي مِثْلَ صَلْصَلَةِ الْجَرَسِ",
        translation="Kadang wahyu datang seperti gemerincing lonceng...",
        api_endpoint="/v1/hadits/shahih_bukhari/2",
    )
    db.add_all([h1, h2])
    db.flush()

    # Sharh Section #1
    s1 = SharhSection(
        work_slug="fathul_bari",
        volume=1,
        page=9,
        title="Syarah Hadis Pertama Innamal A'malu bin-Niyyat",
        arabic_text="قَوْلُهُ (إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ) أَيْ صِحَّةُ الأَعْمَالِ مَشْرُوطٌ بِالنِّيَّةِ",
        translation="Perkataan beliau: amal-amal disyaratkan dengan niat...",
    )
    db.add(s1)
    db.flush()

    # Link Hadith #1 to Sharh Section #1
    link1 = HadithSharhLink(
        hadith_id=h1.id,
        sharh_section_id=s1.id,
        match_method="number_and_text",
        confidence=0.95,
        review_status="verified",
        verified=True,
    )
    db.add(link1)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_query_hadith_number_extraction():
    assert extract_hadith_number_from_query("Tolong jelaskan hadis 1") == 1
    assert extract_hadith_number_from_query("Apa faidah dari hadits no. 2?") == 2
    assert extract_hadith_number_from_query("Jelaskan hadis bukhari #3") == 3
    assert extract_hadith_number_from_query("Bagaimana penjelasan hadis pertama?") == 1
    assert extract_hadith_number_from_query("Apa hukum shalat tanpa wudhu?") is None


def test_citation_validator_and_audit():
    db = TestingSessionLocal()
    val_res = validate_citation_record(db, collection_slug="shahih_bukhari", hadith_number=1, volume=1, page=9)
    assert val_res["is_valid"] is True
    assert val_res["hadith_valid"] is True
    assert val_res["sharh_valid"] is True
    assert val_res["human_verified"] is True
    assert "Ibnu Hajar al-Asqalani" in val_res["citations"]["standard"]

    # Audit anti-halusinasi
    retrieved_h = [{"number": 1}]
    retrieved_s = [{"page": 9}]

    clean_text = "Hadis #1 menjelaskan bahwa amal tergantung niat sebagaimana di Fathul Bari hal. 9."
    audit_clean = audit_ai_response_citations(clean_text, retrieved_h, retrieved_s)
    assert audit_clean["passed"] is True

    hallucinated_text = "Hadis #999 berada di Fathul Bari hal. 8888."
    audit_hallucinated = audit_ai_response_citations(hallucinated_text, retrieved_h, retrieved_s)
    assert audit_hallucinated["passed"] is False
    assert 999 in audit_hallucinated["unverified_hadiths"]
    assert 8888 in audit_hallucinated["unverified_pages"]
    db.close()


@pytest.mark.asyncio
async def test_rag_retrieval_and_synthesis():
    db = TestingSessionLocal()
    retrieval = retrieve_rag_context(db, query="Jelaskan hadis tentang niat", kitab="shahih_bukhari")
    assert len(retrieval["hadiths"]) >= 1
    assert retrieval["hadiths"][0]["number"] == 1
    assert len(retrieval["sharh_sections"]) >= 1
    assert retrieval["sharh_sections"][0]["page"] == 9

    synthesis = await synthesize_rag_response("Jelaskan hadis tentang niat", retrieval, mode="syarah_focus")
    assert "answer" in synthesis
    assert "Innamal A'malu" in synthesis["answer"] or "niat" in synthesis["answer"].lower()
    assert len(synthesis["citations"]) >= 1
    assert synthesis["anti_hallucination_audit"]["passed"] is True
    db.close()


def test_ai_api_status_and_suggestions():
    resp = client.get("/api/v1/ai/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert "features" in data

    resp2 = client.get("/api/v1/ai/suggestions")
    assert resp2.status_code == 200
    sug = resp2.json()
    assert "categories" in sug
    assert len(sug["categories"]) >= 2


def test_ai_api_ask_endpoint():
    payload = {
        "query": "Jelaskan hadis nomor 1 tentang niat",
        "kitab": "shahih_bukhari",
        "hadith_number": 1,
        "mode": "syarah_focus",
    }
    resp = client.post("/api/v1/ai/ask", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "answer" in data
    assert len(data["citations"]) >= 1
    assert data["retrieved_summary"]["detected_hadith_number"] == 1


def test_ai_validate_citation_endpoint():
    payload = {
        "collection_slug": "shahih_bukhari",
        "hadith_number": 1,
        "volume": 1,
        "page": 9,
    }
    resp = client.post("/api/v1/ai/validate-citation", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    assert data["hadith_valid"] is True
    assert data["human_verified"] is True
