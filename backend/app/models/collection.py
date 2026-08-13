import uuid
from sqlalchemy import Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="id", nullable=False)
    total_expected: Mapped[int | None] = mapped_column(Integer)

