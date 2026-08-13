from fastapi import APIRouter
from app.isnad.boundary import segment_hadith
from app.isnad.parser import parse_isnad_chain
from app.sources.adapters.ahmad_sanusi import AhmadSanusiAdapter

router = APIRouter(prefix="/api/v1/hadith", tags=["hadith-intelligence"])

@router.get("/{hadith_id}/intelligence")
def get_hadith_intelligence(hadith_id: str):
    """
    Returns the full Hadith Profile including the Matn, Isnad Graph,
    Variants, Gradings, and Fathul Bari Commentary links.
    """
    # Mocking data for the starter
    return {
        "hadith_id": hadith_id,
        "canonical_key": "bukhari_1",
        "title": "Hadits Niat",
        "matn": {
            "arabic_text": "إنما الأعمال بالنيات وإنما لكل امرئ ما نوى...",
            "translation": "Sesungguhnya amalan itu tergantung niatnya..."
        },
        "isnad_graph": {
            "nodes": [
                {"id": "n1", "name": "مالك", "role": "NARRATOR"},
                {"id": "n2", "name": "نافع", "role": "NARRATOR"},
                {"id": "n3", "name": "ابن عمر", "role": "COMPANION"},
            ],
            "edges": [
                {"from": "n1", "to": "n2", "type": "TEACHER_OF", "term": "عن"},
                {"from": "n2", "to": "n3", "type": "TEACHER_OF", "term": "عن"}
            ]
        },
        "variants": [
            {"id": "var_2", "source": "Muslim", "text": "إنما الأعمال بالنية..."}
        ],
        "gradings": [
            {"source": "Al-Bukhari", "grade": "صحيح"}
        ],
        "commentary": [
            {"source": "Fathul Bari", "topic": "LINGUISTIC", "snippet": "Al-Niyyah is the intention in the heart."}
        ]
    }

@router.get("/external/fetch")
def fetch_external_hadith(collection: str, number: int):
    """
    Fetches a Hadith from the Ahmad Sanusi API and parses its Isnad and Matn boundaries.
    """
    adapter = AhmadSanusiAdapter()
    data = adapter.get_hadith(collection, number)
    
    if data and "arabic_text" in data:
        # Pass to the boundary logic
        segmentation = segment_hadith(data["arabic_text"])
        
        # Parse the isnad
        if segmentation["sanad_text"]:
            parsed_chain = parse_isnad_chain(segmentation["sanad_text"])
        else:
            parsed_chain = {"nodes": [], "edges": []}
            
        data["segmentation"] = segmentation
        data["parsed_isnad"] = parsed_chain
        
    return data
