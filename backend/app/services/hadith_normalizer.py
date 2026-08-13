from app.utils.hash import content_hash


def normalize_hadith(item: dict) -> dict:
    nomor = item.get("nomor")
    if nomor is None:
        raise ValueError("Hadis tidak memiliki nomor.")

    arabic = item.get("arab") or item.get("arabic") or ""
    translation = item.get("terjemah") or item.get("translation") or ""

    return {
        "external_number": int(nomor),
        "arabic_text": arabic,
        "translation": translation,
        "content_hash": content_hash(arabic, translation),
    }


def extract_list_items(payload: dict) -> list[dict]:
    data = payload.get("data") or {}
    if isinstance(data, list):
        return data
    for key in ("hadits", "hadiths", "items", "results"):
        value = data.get(key)
        if isinstance(value, list):
            return value
    return []
