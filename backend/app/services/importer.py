"""JSON dataset import: validate, normalize, deduplicate, persist.

The importer is deliberately all-or-nothing on write errors, but records are
validated individually so one bad row does not reject the whole dataset.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models import ImportBatch, JobPosting, JobSkill
from app.schemas.import_ import ImportErrorItem, ImportResult, OnConflict
from app.schemas.job import JobRecordIn
from app.services.normalization import (
    FRESH_GRADUATE_EXPERIENCE,
    normalize_education,
    normalize_experience,
    normalize_job_type,
    normalize_skills,
)

# Fields copied from a validated record onto a JobPosting (id/skills handled
# separately because they map to the primary key and the association table).
_IMPORTABLE_FIELDS = (
    "company",
    "position",
    "job_type",
    "city",
    "salary_min",
    "salary_max",
    "education",
    "experience",
    "is_fresh_graduate",
    "description",
    "source",
    "source_url",
    "collected_at",
)


def parse_dataset(raw: Any) -> tuple[str, date | None, list[Any]]:
    if not isinstance(raw, dict):
        raise ValueError("JSON 根节点必须是对象")
    records = raw.get("records")
    if not isinstance(records, list):
        raise ValueError("JSON 缺少 records 数组")
    if not records:
        raise ValueError("records 数组为空")

    dataset_name = str(raw.get("dataset_name") or "").strip()
    collected_at: date | None = None
    raw_collected_at = raw.get("collected_at")
    if isinstance(raw_collected_at, str):
        text = raw_collected_at.strip()
        try:
            collected_at = date.fromisoformat(text)
        except ValueError:
            # Dataset-level metadata may also carry a timestamp.
            try:
                collected_at = datetime.fromisoformat(text).date()
            except ValueError:
                collected_at = None
    return dataset_name, collected_at, records


def format_validation_error(exc: ValidationError) -> str:
    parts: list[str] = []
    for error in exc.errors():
        location = ".".join(str(item) for item in error["loc"]) or "record"
        parts.append(f"{location}: {error['msg']}")
    return "; ".join(parts)


def _normalized_payload(record: JobRecordIn, dataset_collected_at: date | None) -> dict[str, Any]:
    payload = record.model_dump(exclude={"id", "skills"})
    payload["job_type"] = normalize_job_type(payload["job_type"])
    payload["education"] = normalize_education(payload["education"])
    payload["experience"] = normalize_experience(payload["experience"])
    if payload["experience"] == FRESH_GRADUATE_EXPERIENCE:
        # A record explicitly tagged as fresh-graduate experience can never be
        # "not accepting fresh graduates"; auto-correct the contradictory flag.
        payload["is_fresh_graduate"] = True
    if payload["collected_at"] is None and dataset_collected_at is not None:
        payload["collected_at"] = dataset_collected_at
    return payload


def import_dataset(
    db: Session,
    raw_dataset: Any,
    *,
    on_conflict: OnConflict = "skip",
    source_file: str | None = None,
) -> ImportResult:
    """Import one dataset object.

    ``on_conflict`` controls records whose ``id`` already exists:
    ``skip`` ignores them, ``update`` replaces them, ``fail`` reports them as
    errors. Duplicate ids *inside the same file* are always reported as errors.
    """
    dataset_name, dataset_collected_at, records = parse_dataset(raw_dataset)

    imported = updated = skipped = failed = 0
    errors: list[ImportErrorItem] = []
    seen_ids: set[str] = set()

    for row_number, raw_record in enumerate(records, start=1):
        raw_id = raw_record.get("id") if isinstance(raw_record, dict) else None

        if not isinstance(raw_record, dict):
            failed += 1
            errors.append(
                ImportErrorItem(
                    row=row_number,
                    record_id=str(raw_id) if raw_id is not None else None,
                    message="记录必须是 JSON 对象",
                )
            )
            continue

        try:
            record = JobRecordIn.model_validate(raw_record)
        except ValidationError as exc:
            failed += 1
            errors.append(
                ImportErrorItem(
                    row=row_number,
                    record_id=str(raw_id) if raw_id is not None else None,
                    message=format_validation_error(exc),
                )
            )
            continue

        if record.id in seen_ids:
            failed += 1
            errors.append(
                ImportErrorItem(
                    row=row_number,
                    record_id=record.id,
                    message="同一文件内 id 重复",
                )
            )
            continue
        seen_ids.add(record.id)

        payload = _normalized_payload(record, dataset_collected_at)
        skills = normalize_skills(record.skills)

        existing = db.get(JobPosting, record.id)
        if existing is not None:
            if on_conflict == "skip":
                skipped += 1
            elif on_conflict == "fail":
                failed += 1
                errors.append(
                    ImportErrorItem(
                        row=row_number,
                        record_id=record.id,
                        message="数据库中已存在该 id（on_conflict=fail）",
                    )
                )
            else:
                for field in _IMPORTABLE_FIELDS:
                    setattr(existing, field, payload[field])
                # Delete old skills and flush before inserting new ones: the
                # (job_id, skill_name) unique constraint would otherwise be
                # violated by INSERT-before-DELETE ordering on update.
                existing.skills.clear()
                db.flush()
                existing.skills.extend(
                    JobSkill(skill_name=skill) for skill in skills
                )
                updated += 1
            continue

        db.add(
            JobPosting(
                id=record.id,
                **payload,
                skills=[JobSkill(skill_name=skill) for skill in skills],
            )
        )
        imported += 1

    batch = ImportBatch(
        dataset_name=dataset_name,
        source_file=source_file,
        on_conflict=on_conflict,
        total_records=len(records),
        imported=imported,
        updated=updated,
        skipped=skipped,
        failed=failed,
    )
    db.add(batch)
    db.flush()
    batch_id = batch.id
    db.commit()

    return ImportResult(
        dataset_name=dataset_name,
        source_file=source_file,
        total_records=len(records),
        imported=imported,
        updated=updated,
        skipped=skipped,
        failed=failed,
        errors=errors,
        batch_id=batch_id,
    )


__all__ = ["format_validation_error", "import_dataset", "parse_dataset"]
