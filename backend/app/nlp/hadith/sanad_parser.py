import re
from typing import List, Dict, Any

# Triggers for narrators
NARRATOR_TRIGGERS = [
    "حدثنا",
    "حدثني",
    "أخبرنا",
    "عن",
    "قال",
    "سمعت"
]

def extract_narrator_candidates(text: str) -> List[Dict[str, Any]]:
    """
    Detects potential narrators based on typical Hadith chain triggers.
    This is a heuristic-based extraction. In a real scenario, this would be backed by NER.
    """
    candidates = []
    
    # Simple heuristic: Look for trigger + following 2-3 words.
    for trigger in NARRATOR_TRIGGERS:
        # Regex to find trigger followed by 1 to 3 words
        pattern = re.compile(rf"{trigger}\s+([\w\u0600-\u06FF]+\s+[\w\u0600-\u06FF]+(?:\s+[\w\u0600-\u06FF]+)?)")
        
        for match in pattern.finditer(text):
            candidate_name = match.group(1).strip()
            candidates.append({
                "surface": candidate_name,
                "trigger": trigger,
                "start_char": match.start(1),
                "end_char": match.end(1),
                "entity_type": "NARRATOR_CANDIDATE"
            })
            
    return candidates
