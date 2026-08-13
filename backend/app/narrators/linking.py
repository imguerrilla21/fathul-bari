from typing import Dict, Any, Optional

# Mock alias database for demonstration
ALIAS_DB = {
    "ابن عمر": {
        "canonical_name": "عبد الله بن عمر بن الخطاب",
        "entity_id": "person_ibn_umar_123"
    },
    "مالك": {
        "canonical_name": "مالك بن أنس",
        "entity_id": "person_malik_123"
    },
    "نافع": {
        "canonical_name": "نافع مولى ابن عمر",
        "entity_id": "person_nafi_123"
    }
}

def resolve_narrator_alias(surface_name: str) -> Optional[Dict[str, Any]]:
    """
    Attempts to link a surface name (e.g., 'ابن عمر') to a canonical narrator entity.
    """
    normalized = surface_name.strip()
    
    if normalized in ALIAS_DB:
        match = ALIAS_DB[normalized]
        return {
            "surface": surface_name,
            "candidate_entity": match["entity_id"],
            "canonical_name": match["canonical_name"],
            "confidence": 0.95,
            "resolution_method": "ALIAS_MATCH"
        }
        
    return {
        "surface": surface_name,
        "candidate_entity": None,
        "canonical_name": None,
        "confidence": 0.0,
        "resolution_method": "UNKNOWN"
    }
