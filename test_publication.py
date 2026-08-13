import httpx
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_tests():
    print("--- Stage 47 Publication Pipeline Verification ---")
    
    # 1. Create a Publication (Draft)
    r = httpx.post(f"{BASE_URL}/publications", json={
        "project_id": "PROJECT-123",
        "title": "Makna Niat dalam Fathul Bari",
        "slug": f"makna-niat-{int(time.time())}",
        "content_type": "RESEARCH_ARTICLE",
        "language": "id"
    })
    print(f"POST /publications: {r.status_code}")
    pub = r.json()
    pub_id = pub["id"]
    slug = pub["slug"]
    print(json.dumps(pub, indent=2))
    
    # 2. Create a Version
    r = httpx.post(f"{BASE_URL}/publications/{pub_id}/versions", json={
        "content": "Full article draft text here...",
        "change_summary": "Initial draft from research workspace"
    })
    print(f"POST /versions: {r.status_code}")
    ver = r.json()
    ver_id = ver["id"]
    
    # 3. Add Content Block (Paragraph)
    r = httpx.post(f"{BASE_URL}/publications/versions/{ver_id}/blocks", json={
        "block_type": "PARAGRAPH",
        "content": "Ibn Hajar menjelaskan bahwa niat sangat menentukan amal.",
        "block_order": 1
    })
    print(f"POST /blocks: {r.status_code}")
    block = r.json()
    block_id = block["id"]
    
    # 4. Link Evidence to the Block
    r = httpx.post(f"{BASE_URL}/publications/blocks/{block_id}/evidence", json={
        "evidence_type": "FATHUL_BARI_PASSAGE",
        "evidence_id": "FB-VOL1-P184-CHUNK12",
        "relation": "SUPPORTED_BY"
    })
    print(f"POST /evidence: {r.status_code}")
    
    # 5. Report an Editorial Issue
    r = httpx.post(f"{BASE_URL}/publications/{pub_id}/issues", json={
        "block_id": block_id,
        "issue_type": "MISSING_CITATION",
        "severity": "MEDIUM",
        "description": "Please add explicit citation format for this claim."
    })
    print(f"POST /issues: {r.status_code}")
    
    # 6. Check Issues List
    r = httpx.get(f"{BASE_URL}/publications/{pub_id}/issues")
    print(f"GET /issues: {r.status_code}")
    issues = r.json()
    print(f"Total issues: {len(issues)}")
    
    # 7. Approve & Publish
    r = httpx.post(f"{BASE_URL}/publications/{pub_id}/publish")
    print(f"POST /publish: {r.status_code}")
    
    # 8. Public Reader Request
    r = httpx.get(f"{BASE_URL}/public/publications/{slug}")
    print(f"GET /public/publications/{slug}: {r.status_code}")
    print(json.dumps(r.json(), indent=2))

if __name__ == "__main__":
    run_tests()
