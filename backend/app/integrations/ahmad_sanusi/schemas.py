from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class HadithDTO(BaseModel):
    """Data Transfer Object untuk Hadis dari provider Ahmad Sanusi API."""
    external_id: str
    collection_slug: str
    book_number: Optional[int] = 1
    hadith_number: str
    arabic_text: str
    narrator_text: Optional[str] = None
    grade: Optional[str] = "Sahih"
    source_url: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = {}


class CollectionDTO(BaseModel):
    """Data Transfer Object untuk Koleksi Kitab Hadis."""
    slug: str
    name_ar: str
    name_id: str
    total_hadiths: int = 7000


class BookDTO(BaseModel):
    """Data Transfer Object untuk Bab/Kitab Hadis."""
    external_id: str
    collection_slug: str
    number: int
    name_ar: str
    name_id: str
