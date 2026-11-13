"""ORM models for job postings and their skills."""

from app.models.job import JobPosting
from app.models.skill import JobSkill

__all__ = ["JobPosting", "JobSkill"]
