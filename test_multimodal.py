import httpx
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.multimodal import SourcePageEntity, PageRegionEntity, OCRBlockEntity

def seed_db():
    db = SessionLocal()
    # Create page
    page = SourcePageEntity(
        document_id="doc-123",
        volume_number=1,
        page_number=184,
        image_uri="s3://book/vol1/page184.webp",
        width=2480,
        height=3508
    )
    db.add(page)
    db.commit()

    # Create region
    region = PageRegionEntity(
        page_id=page.id,
        region_type="MAIN_TEXT",
        x1=420, y1=350, x2=2070, y2=3150,
        reading_order=1
    )
    db.add(region)
    db.commit()

    # Create block
    block = OCRBlockEntity(
        region_id=region.id,
        raw_text="البيه",  # Error: Should be النية
        normalized_text="البيه",
        ocr_confidence=0.61,
        ocr_engine="tesseract"
    )
    db.add(block)
    db.commit()

    return page.id, region.id, block.id

if __name__ == "__main__":
    print("--- Stage 41 Multimodal Verification ---")
    page_id, region_id, block_id = seed_db()
    print(f"Seeded Page: {page_id}, Region: {region_id}, Block: {block_id}")

    base_url = "http://127.0.0.1:8000/api/v1"

    # 1. Test get page
    r = httpx.get(f"{base_url}/source/pages/{page_id}")
    print("\nGET Page:", r.status_code)
    
    # 2. Test get regions
    r = httpx.get(f"{base_url}/source/pages/{page_id}/regions")
    print("GET Regions:", r.status_code, len(r.json()))
    
    # 3. Submit Correction
    req = {
        "block_id": block_id,
        "corrected_text": "النية",
        "reviewer_id": "usr-123",
        "reason": "Visual verification"
    }
    r = httpx.post(f"{base_url}/source/corrections", json=req)
    print("POST Correction:", r.status_code)
    
    # 4. Search for the correction
    search_req = {
        "query": "النية",
        "page_id": page_id
    }
    r = httpx.post(f"{base_url}/rag/multimodal-search", json=search_req)
    print("POST Multimodal Search:", r.status_code)
    res = r.json().get("results", [])
    if res:
        print("Search Found Match:", res[0]["text"])
        print("BBox:", res[0]["bbox"])
    else:
        print("Search Found No Matches!")
