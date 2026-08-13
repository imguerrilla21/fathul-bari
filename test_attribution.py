import httpx
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.attribution import ScholarEntity, ScholarAliasEntity, AttributedClaimEntity

def seed_db():
    db = SessionLocal()
    # Create scholars
    ibn_hajar = ScholarEntity(canonical_name="Ibn Hajar al-Asqalani")
    al_nawawi = ScholarEntity(canonical_name="al-Nawawi")
    db.add_all([ibn_hajar, al_nawawi])
    db.commit()

    # Create aliases
    ibn_hajar_alias = ScholarAliasEntity(scholar_id=ibn_hajar.id, alias="ابن حجر")
    al_nawawi_alias = ScholarAliasEntity(scholar_id=al_nawawi.id, alias="النووي")
    db.add_all([ibn_hajar_alias, al_nawawi_alias])
    db.commit()

    # Create a claim where Ibn Hajar quotes al-Nawawi
    claim = AttributedClaimEntity(
        passage_id="P88421",
        claim_text="An intention distinguishes acts of worship.",
        speaker_id=al_nawawi.id,
        reporter_id=ibn_hajar.id,
        relation="QUOTES"
    )
    db.add(claim)
    db.commit()

    return ibn_hajar.id, al_nawawi.id, claim.id

if __name__ == "__main__":
    print("--- Stage 42 Scholarly Attribution Verification ---")
    ibn_hajar_id, al_nawawi_id, claim_id = seed_db()
    print(f"Seeded Scholars - Ibn Hajar: {ibn_hajar_id}, al-Nawawi: {al_nawawi_id}")

    base_url = "http://127.0.0.1:8000/api/v1/attribution"

    # 1. Test Analyze Attribution
    req = {
        "passage_id": "P88421",
        "text": "وقال النووي إنما الأعمال بالنيات..."
    }
    r = httpx.post(f"{base_url}/analyze", json=req)
    print("\nPOST Analyze:", r.status_code)
    analyze_res = r.json()
    print(f"Detected Speaker: {analyze_res['speaker']['name']} (ID: {analyze_res['speaker']['id']})")
    
    # 2. Test Get Claim
    r = httpx.get(f"{base_url}/claims/{claim_id}")
    print("\nGET Claim:", r.status_code)
    
    # 3. Test Graph
    r = httpx.get(f"{base_url}/graph/P88421")
    print("\nGET Graph:", r.status_code)
    graph = r.json()
    print(f"Nodes: {len(graph['nodes'])}, Edges: {len(graph['edges'])}")
    if graph['edges']:
        print(f"Edge Relation: {graph['edges'][0]['type']}")
        
    # 4. Test Verification (Prevent False Attribution)
    # E.g. we expected Ibn Hajar but found al-Nawawi
    verify_req = {
        "claim_id": claim_id,
        "detected_speaker_id": al_nawawi_id,
        "expected_speaker_id": ibn_hajar_id # Expecting Ibn Hajar
    }
    r = httpx.post(f"{base_url}/verify", json=verify_req)
    print("\nPOST Verify Attribution (False Attribution case):", r.status_code)
    print("Verification Status:", r.json()["status"])
