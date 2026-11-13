"""Job-skill association ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.job import JobPosting


class JobSkill(Base):
    """One skill required by one job posting.

    Storing skills in a separate table makes frequency ranking and
    per-job-type comparisons simple, and avoids a JSON column that SQLite
    cannot aggregate efficiently.
    """

    __tablename__ = "job_skills"
    __table_args__ = (
        UniqueConstraint("job_id", "skill_name", name="uq_job_skills_job_skill"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(
        ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)

    job: Mapped["JobPosting"] = relationship(back_populates="skills")

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<JobSkill job_id={self.job_id!r} skill={self.skill_name!r}>"
