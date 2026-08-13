from typing import Optional

# Very basic dictionary for demonstration purposes.
ROOT_DICT = {
    "نية": "ن و ي",
    "نوى": "ن و ي",
    
    "عمل": "ع م ل",
    
    "قصد": "ق ص د",
    
    "ابن": "ب ن ي",
    "حجر": "ح ج ر",
}

def extract_arabic_root(lemma: str) -> Optional[str]:
    """
    Returns the 3 or 4 letter root for a given Arabic lemma.
    """
    return ROOT_DICT.get(lemma)
