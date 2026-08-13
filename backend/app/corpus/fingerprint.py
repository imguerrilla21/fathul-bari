import hashlib

def generate_edition_fingerprint(title: str, publisher: str, editor: str, year: int, volume_count: int) -> str:
    payload = f"{title}|{publisher}|{editor}|{year}|{volume_count}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

def generate_page_fingerprint(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()

def generate_passage_fingerprint(edition_id: str, volume: int, page: int, normalized_text: str) -> str:
    payload = f"{edition_id}|{volume}|{page}|{normalized_text}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

def generate_hadith_matn_fingerprint(normalized_matn: str) -> str:
    return hashlib.sha256(normalized_matn.encode('utf-8')).hexdigest()
