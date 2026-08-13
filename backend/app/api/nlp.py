from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.nlp.arabic.tokenizer import tokenize_arabic
from app.nlp.arabic.lemmatizer import lemmatize_arabic
from app.nlp.arabic.roots import extract_arabic_root
from app.nlp.hadith.sanad_parser import extract_narrator_candidates
from app.nlp.hadith.terminology import extract_hadith_terminology
from app.retrieval.hybrid import perform_hybrid_arabic_search

router = APIRouter(prefix="/api/v1", tags=["arabic-nlp"])

class AnalyzeTextRequest(BaseModel):
    text: str

@router.post("/nlp/arabic/analyze")
def analyze_arabic_text(req: AnalyzeTextRequest):
    """
    Analyzes Arabic text, returning tokens, normalized forms, lemmas, roots,
    as well as entity extractions (like narrators and terminology).
    """
    tokens = tokenize_arabic(req.text)
    
    # Enrich tokens with lemmas and roots
    for token in tokens:
        lemma = lemmatize_arabic(token["normalized"])
        root = extract_arabic_root(lemma) if lemma else None
        
        token["lemma"] = lemma
        if root:
            token["root"] = root
            
    # Extract specific entities
    narrators = extract_narrator_candidates(req.text)
    terms = extract_hadith_terminology(req.text)
    
    return {
        "tokens": tokens,
        "entities": {
            "narrators": narrators,
            "terms": terms
        }
    }


@router.get("/search/arabic")
def search_arabic(
    q: str = Query(..., description="The query string to search for"),
    mode: str = Query("hybrid", description="Search mode (e.g., hybrid, exact, semantic)"),
    source: Optional[str] = Query(None, description="Filter by source (e.g., fathul_bari)")
):
    """
    Performs a rich hybrid search on Arabic text using Exact, Lexical, Lemma, and Semantic scoring.
    """
    if mode == "hybrid":
        return perform_hybrid_arabic_search(query=q, source_filter=source)
    else:
        # For this starter, we just default to hybrid search anyway
        return perform_hybrid_arabic_search(query=q, source_filter=source)


@router.get("/nlp/concordance")
def get_concordance(
    lemma: str = Query(..., description="The lemma to search for concordance")
):
    """
    Returns concordance data for a given lemma.
    """
    # Mocking concordance response
    root = extract_arabic_root(lemma)
    
    return {
        "lemma": lemma,
        "root": root or "UNKNOWN",
        "occurrences": 1247 if lemma == "نية" else 42,
        "results": [
            {
                "snippet": "إنما الأعمال بالنيات وإنما لكل امرئ ما نوى",
                "source": "Sahih Bukhari #1"
            },
            {
                "snippet": "النية محلها القلب",
                "source": "Fathul Bari, Vol 1, Page 12"
            }
        ]
    }
