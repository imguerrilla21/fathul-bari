from typing import Optional

# Very basic dictionary for demonstration purposes.
# In a real system, use an Arabic morphological analyzer like Farasa, CamelTools, or Qalsadi.
LEMMA_DICT = {
    "بالنيات": "نية",
    "النيات": "نية",
    "نيات": "نية",
    "النية": "نية",
    "نية": "نية",
    "نيته": "نية",
    
    "نوى": "نوى",
    "ينوي": "نوى",
    
    "الاعمال": "عمل",
    "اعمال": "عمل",
    "العمل": "عمل",
    "عمل": "عمل",
    "يعمل": "عمل",
    "اعمل": "عمل",
}

def lemmatize_arabic(normalized_token: str) -> Optional[str]:
    """
    Returns the lemma of a given normalized Arabic word.
    """
    return LEMMA_DICT.get(normalized_token, normalized_token)
