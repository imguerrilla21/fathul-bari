import httpx
from typing import Dict, Any
from .base import HadithSourceAdapter

class AhmadSanusiAdapter(HadithSourceAdapter):
    """
    Adapter for the Ahmad Sanusi Hadits API.
    See: https://github.com/AhmadSanusi/hadits-api
    """
    
    BASE_URL = "https://hadis-api-id.vercel.app/hadith"

    def get_hadith(self, collection: str, number: int) -> Dict[str, Any]:
        """
        Fetches a hadith by collection name and number.
        Valid collections: abu-dawud, ahmad, bukhari, darimi, ibnu-majah, malik, muslim, nasai, tirmidzi
        """
        url = f"{self.BASE_URL}/{collection}?range={number}-{number}"
        response = httpx.get(url)
        
        if response.status_code == 200:
            data = response.json()
            # Standardize payload structure
            if data and "items" in data:
                hadiths = data["items"]
                if hadiths:
                    raw_hadith = hadiths[0]
                    return {
                        "external_id": f"{collection}_{number}",
                        "collection": data.get("name"),
                        "number": raw_hadith.get("number"),
                        "arabic_text": raw_hadith.get("arab"),
                        "translation": raw_hadith.get("id"),
                        "raw_payload": raw_hadith
                    }
        
        return {}

    def search(self, query: str) -> Dict[str, Any]:
        """The Ahmad Sanusi API does not natively support search in this simple Vercel wrapper. 
        We would typically download the corpus and index it locally, or use a different endpoint."""
        pass
