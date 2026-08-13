from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class ArabicNLPProvider(ABC):
    """
    Abstract Base Class for Arabic NLP operations.
    Allows swappable implementations (Local, External API, Hybrid).
    """

    @abstractmethod
    def normalize(self, text: str) -> str:
        """Normalizes Unicode Arabic characters (e.g., Tatweel removal, Alef/Ya standardization)."""
        pass
        
    @abstractmethod
    def remove_diacritics(self, text: str) -> str:
        """Removes Arabic vowel marks (harakat) while preserving base letters."""
        pass

    @abstractmethod
    def tokenize(self, text: str) -> List[Dict[str, Any]]:
        """
        Tokenizes text with clitic-awareness.
        Returns a list of token dictionaries containing surface, normalized, start_char, end_char.
        """
        pass

    @abstractmethod
    def lemmatize(self, token: str) -> str:
        """Returns the lemma (dictionary form) for a given token."""
        pass

    @abstractmethod
    def root(self, token: str) -> str:
        """Returns the 3 or 4 letter Arabic root for a given token."""
        pass

    @abstractmethod
    def analyze(self, token: str) -> Dict[str, Any]:
        """
        Provides rich morphological analysis (POS, Gender, Number, Case, etc.).
        """
        pass
        
    @abstractmethod
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts named entities from the given text (Person, Book, Location, etc.).
        Returns list of dictionaries containing surface, entity_type, start_char, end_char.
        """
        pass
