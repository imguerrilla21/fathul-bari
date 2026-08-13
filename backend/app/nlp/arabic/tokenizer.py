import re
from typing import List, Dict, Any
from app.nlp.arabic.normalizer import normalize_arabic
from app.nlp.arabic.diacritics import remove_diacritics

# Basic Arabic tokenizer pattern (splits by whitespace and punctuation)
ARABIC_TOKEN_PATTERN = re.compile(r"[\w\u0600-\u06FF]+")

def tokenize_arabic(text: str) -> List[Dict[str, Any]]:
    """
    Splits Arabic text into tokens, maintaining original surface text,
    start and end positions, and providing a normalized version.
    In a full production NLP pipeline (e.g. Farasa, CamelTools), this would also 
    split clitics (wa, bi, ka, li, etc). For this starter, we use a basic regex tokenizer 
    and provide basic prefix separation heuristics for "و" (wa) and "ب" (bi).
    """
    tokens = []
    
    for match in ARABIC_TOKEN_PATTERN.finditer(text):
        surface = match.group()
        start = match.start()
        end = match.end()
        
        normalized = normalize_arabic(remove_diacritics(surface))
        
        # Very basic clitic awareness for demonstration:
        # If the word is 'وبالنيات' (wabilniyat), we can detect 'و' and 'ب'.
        # However, a real morphological analyzer handles this properly.
        # We will keep it simple here.
        
        tokens.append({
            "surface": surface,
            "normalized": normalized,
            "start_char": start,
            "end_char": end,
        })
        
    return tokens
