import re

# Regex for Arabic vowel marks (harakat)
ARABIC_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)

def remove_diacritics(text: str) -> str:
    """
    Strips diacritics (harakat) from Arabic text, returning the bare consonantal text.
    Useful for search indexing where users might type without diacritics.
    """
    return ARABIC_DIACRITICS.sub("", text)
