"""Job posting request/response schemas."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class JobBase(BaseModel):
    """Fields shared by the import record and the API response."""

    company: str = Field(min_length=1, max_length=200)
    position: str = Field(min_length=1, max_length=200)
    job_type: str = Field(default="其他", max_length=50)
    city: str = Field(default="未知", max_length=50)
    salary_min: int | None = Field(default=None, ge=0, le=1_000_000)
    salary_max: int | None = Field(default=None, ge=0, le=1_000_000)
    education: str = Field(default="不限", max_length=30)
    experience: str = Field(default="不限", max_length=30)
    is_fresh_graduate: bool = False
    description: str = ""
    source: str = Field(default="", max_length=100)
    source_url: str = Field(default="", max_length=500)
    collected_at: date | None = None
    skills: list[str] = Field(default_factory=list)

    @field_validator("company", "position", "job_type", "city", "education", "experience")
    @classmethod
    def _strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("字段不能为空")
        return value

    @field_validator("skills")
    @classmethod
    def _clean_skills(cls, value: list[str]) -> list[str]:
        cleaned = [skill.strip() for skill in value if isinstance(skill, str) and skill.strip()]
        if len(cleaned) > 50:
            raise ValueError("单个岗位的技能数量不能超过 50 个")
        return cleaned

    @model_validator(mode="after")
    def _check_salary_range(self) -> "JobBase":
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValueError("salary_min 不能大于 salary_max")
        return self


class JobRecordIn(JobBase):
    """One record inside the import JSON file."""

    id: str = Field(min_length=1, max_length=64)

    @field_validator("id")
    @classmethod
    def _strip_id(cls, value: str) -> str:
        return value.strip()


class JobOut(JobBase):
    """A job posting returned by the query API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    skills: list[str] = Field(default_factory=list)


class JobListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[JobOut]


class FilterMeta(BaseModel):
    """Distinct values used to populate frontend filters."""

    job_types: list[str]
    educations: list[str]
    experiences: list[str]
    cities: list[str]
    skills: list[str]
