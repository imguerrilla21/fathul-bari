import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Hadith(Base):
    __tablename__ = "hadiths"

    __table_args__ = (
        UniqueConstraint("collection_id", "external_number", name="uq_hadith_collection_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("collections.id"), nullable=False, index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("sources.id"), nullable=False, index=True)
    external_number: Mapped[int] = mapped_column(Integer, nullable=False)
    arabic_text: Mapped[str | None] = mapped_column(Text)
    translation: Mapped[str | None] = mapped_column(Text)
    api_endpoint: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

