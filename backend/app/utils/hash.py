import hashlib


def content_hash(arabic: str | None, translation: str | None) -> str:
    raw = f"{arabic or ''}||{translation or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
