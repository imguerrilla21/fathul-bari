from typing import List, Dict, Any
from app.models.research import ResearchEvidenceEntity

# Mocked tool implementations for the starter
# In a real implementation, these would query the database/search engine.

def search_hadith(query: str) -> List[Dict[str, Any]]:
    return [{"id": "bukhari_1", "text": "إنما الأعمال بالنيات", "source": "Sahih al-Bukhari"}]

def get_commentary(query: str, source_id: str) -> List[Dict[str, Any]]:
    return [
        {"id": "fb_1", "text": "Kata Niyyat adalah bentuk jamak dari Niyyah...", "source": "Fathul Bari"}
    ]
