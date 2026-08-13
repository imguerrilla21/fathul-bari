import uuid
from typing import Any


def to_uuid(val: Any) -> uuid.UUID | None:
    """Mengonversi nilai str/uuid/int ke uuid.UUID dengan aman."""
    if val is None:
        return None
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val).strip())
    except Exception:
        return None
