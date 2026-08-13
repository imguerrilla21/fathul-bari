import httpx
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine

if __name__ == "__main__":
    print("--- Stage 44 Workspace Verification ---")
    base_url = "http://127.0.0.1:8000/api/v1/workspace"

    # 1. Create Project
    req = {
        "title": "Studi Syarah Hadis Niat",
        "description": "Project test"
    }
    r = httpx.post(f"{base_url}/projects", json=req)
    print("POST Create Project:", r.status_code)
    project_id = r.json()["id"]
    
    # 2. Create Annotation
    ann_req = {
        "passage_id": "P88421",
        "selected_text": "إنما الأعمال بالنيات",
        "start_offset": 122,
        "end_offset": 145,
        "anchor_before": "قال رسول الله ",
        "anchor_after": " وإنما لكل امرئ",
        "comment": "Definisi niat"
    }
    r = httpx.post(f"{base_url}/projects/{project_id}/annotations", json=ann_req)
    print("POST Create Annotation:", r.status_code)
    annotation_id = r.json()["id"]
    
    # 3. Test Annotation Recovery
    # Imagine OCR shifted text so start_offset is now 150 instead of 122
    shifted_text = " "*28 + "قال رسول الله إنما الأعمال بالنيات وإنما لكل امرئ"
    recover_req = {
        "annotation_id": annotation_id,
        "current_passage_text": shifted_text
    }
    r = httpx.post(f"{base_url}/annotations/recover", json=recover_req)
    print("POST Recover Annotation:", r.status_code)
    res = r.json()
    print(f"Status: {res['status']}, New Start Offset: {res['start_offset']}")
    
    if res['start_offset'] == 42: # " "*28 + 14 chars for "قال رسول الله " = 42
        print("Recovery was SUCCESSFUL! Shifted offset automatically resolved.")
    
    # 4. Create Bookmark
    bm_req = {
        "target_type": "HADITH",
        "target_id": "H001",
        "title": "Bookmark Hadith Niat"
    }
    r = httpx.post(f"{base_url}/projects/{project_id}/bookmarks", json=bm_req)
    print("POST Create Bookmark:", r.status_code)
