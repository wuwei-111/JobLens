"""Job posting ORM model."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.skill import JobSkill


class JobPosting(Base):
    """A normalized job posting record.

    ``salary_min`` / ``salary_max`` are monthly salaries in CNY. Records with
    "面议" (negotiable) keep both bounds as NULL rather than 0, so they are
    excluded from salary statistics instead of dragging the average down.
    """

    __tablename__ = "job_postings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    position: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False, default="其他", index=True)
    city: Mapped[str] = mapped_column(String(50), nullable=False, default="未知", index=True)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    education: Mapped[str] = mapped_column(String(30), nullable=False, default="不限", index=True)
    experience: Mapped[str] = mapped_column(String(30), nullable=False, default="不限", index=True)
    is_fresh_graduate: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    source_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    collected_at: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    skills: Mapped[list["JobSkill"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="JobSkill.skill_name",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<JobPosting id={self.id!r} position={self.position!r}>"
