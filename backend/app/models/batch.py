"""One row per import run, kept for reproducibility and delivery evidence."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ImportBatch(Base):
    """Summary of one JSON import attempt.

    The per-record errors are returned in the import response, not stored here.
    Keeping the counts and the source file name is enough to reproduce a run and
    to explain why a dataset produced more or fewer rows than expected.
    """

    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    source_file: Mapped[str | None] = mapped_column(String(255), nullable=True)
    on_conflict: Mapped[str] = mapped_column(String(10), nullable=False, default="skip")
    total_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    imported: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<ImportBatch id={self.id!r} imported={self.imported!r}>"
