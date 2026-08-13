from abc import ABC, abstractmethod
from typing import Dict, Any

class HadithSourceAdapter(ABC):
    """
    Base contract for all Hadith Source Adapters.
    Adapters fetch raw data from external APIs or local files and parse it into a standard format.
    """

    @abstractmethod
    def get_hadith(self, external_id: str) -> Dict[str, Any]:
        """Fetches a single hadith by its external ID."""
        pass
        
    @abstractmethod
    def search(self, query: str) -> Dict[str, Any]:
        """Searches the source for a specific query."""
        pass
