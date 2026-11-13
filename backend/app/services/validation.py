"""Read-only dataset preflight.

The same checks run in three places:

* ``POST /api/v1/imports/validate`` before a real import;
* ``python -m scripts.check_dataset`` offline;
* the quality summary endpoint (database-level checks).

Validation never writes to SQLite. It reuses the import schema and
normalization vocabulary, so the preflight cannot silently disagree with the
actual importer.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from pydantic import ValidationError

from app.schemas.import_ import ImportErrorItem, ValidationReport
from app.schemas.job import JobRecordIn
from app.schemas.quality import ValueCount
from app.services.importer import format_validation_error, parse_dataset
from app.services.normalization import (
    normalize_education,
    normalize_experience,
    normalize_skills,
)
from app.services.stats import EDUCATION_ORDER, EXPERIENCE_ORDER

CANONICAL_EDUCATION = set(EDUCATION_ORDER) - {"未知"}
CANONICAL_EXPERIENCE = set(EXPERIENCE_ORDER) - {"未知"}

REQUIRED_FIELDS = (
    "id",
    "company",
    "position",
    "job_type",
    "city",
    "education",
    "experience",
    "source",
    "source_url",
    "collected_at",
)

SALARY_LOW = 2_000
SALARY_HIGH = 100_000
MAX_SKILLS = 10
MAX_WARNING_ITEMS = 200


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _sorted_counts(counter: Counter[str]) -> list[ValueCount]:
    return [
        ValueCount(value=value, count=count)
        for value, count in sorted(
            counter.items(), key=lambda item: (-item[1], item[0])
        )
    ]


def validate_dataset(
    raw_dataset: Any,
    *,
    existing_ids: set[str] | None = None,
) -> ValidationReport:
    """Validate a dataset object without touching the database.

    ``existing_ids`` is optional; when supplied it is used by the API preflight
    to tell the user how many records already exist. The offline script leaves
    it empty.
    """
    dataset_name, _, records = parse_dataset(raw_dataset)

    missing_fields: Counter[str] = Counter({field: 0 for field in REQUIRED_FIELDS})
    errors: list[ImportErrorItem] = []
    warnings: list[ImportErrorItem] = []
    warning_count = 0

    def add_warning(
        message: str,
        *,
        row: int | None = None,
        record_id: str | None = None,
    ) -> None:
        nonlocal warning_count
        warning_count += 1
        if len(warnings) < MAX_WARNING_ITEMS:
            warnings.append(
                ImportErrorItem(row=row, record_id=record_id, message=message)
            )

    valid_records: list[tuple[int, JobRecordIn]] = []
    seen_ids: set[str] = set()
    duplicate_ids = 0

    for row_number, raw_record in enumerate(records, start=1):
        raw_id = raw_record.get("id") if isinstance(raw_record, dict) else None

        if not isinstance(raw_record, dict):
            errors.append(
                ImportErrorItem(
                    row=row_number,
                    record_id=str(raw_id) if raw_id is not None else None,
                    message="记录必须是 JSON 对象",
                )
            )
            continue

        for field in REQUIRED_FIELDS:
            if _is_blank(raw_record.get(field)):
                missing_fields[field] += 1

        try:
            record = JobRecordIn.model_validate(raw_record)
        except ValidationError as exc:
            errors.append(
                ImportErrorItem(
                    row=row_number,
                    record_id=str(raw_id) if raw_id is not None else None,
                    message=format_validation_error(exc),
                )
            )
            continue

        if record.id in seen_ids:
            duplicate_ids += 1
            errors.append(
                ImportErrorItem(
                    row=row_number,
                    record_id=record.id,
                    message="同一文件内 id 重复",
                )
            )
            continue
        seen_ids.add(record.id)
        valid_records.append((row_number, record))

    unknown_education: Counter[str] = Counter()
    unknown_experience: Counter[str] = Counter()
    source_urls: Counter[str] = Counter()
    salary_missing = 0
    salary_single_bound = 0
    salary_outliers = 0
    empty_skills = 0
    over_limit_skills = 0
    duplicate_skill_entries = 0
    demo_records = 0

    for row_number, record in valid_records:
        education = normalize_education(record.education)
        if education not in CANONICAL_EDUCATION:
            unknown_education[education] += 1

        experience = normalize_experience(record.experience)
        if experience not in CANONICAL_EXPERIENCE:
            unknown_experience[experience] += 1

        if record.salary_min is None and record.salary_max is None:
            salary_missing += 1
        elif (record.salary_min is None) != (record.salary_max is None):
            salary_single_bound += 1

        known_bounds = [
            value
            for value in (record.salary_min, record.salary_max)
            if value is not None
        ]
        if any(
            value < SALARY_LOW or value > SALARY_HIGH for value in known_bounds
        ):
            salary_outliers += 1
            add_warning(
                f"薪资疑似异常：{record.salary_min}–{record.salary_max} 元/月",
                row=row_number,
                record_id=record.id,
            )

        if not record.skills:
            empty_skills += 1
            add_warning(
                "技能为空，建议补充 1–10 个标准技能词",
                row=row_number,
                record_id=record.id,
            )
        else:
            if len(record.skills) > MAX_SKILLS:
                over_limit_skills += 1
                add_warning(
                    f"技能数 {len(record.skills)} 超过规范上限 {MAX_SKILLS} 项",
                    row=row_number,
                    record_id=record.id,
                )
            normalized_skills = normalize_skills(record.skills)
            if len(normalized_skills) < len(record.skills):
                duplicate_skill_entries += 1
                add_warning(
                    "技能存在重复（大小写或空格不同），导入时会去重",
                    row=row_number,
                    record_id=record.id,
                )
            long_skills = [skill for skill in record.skills if len(skill) > 80]
            if long_skills:
                add_warning(
                    f"技能名超过 80 字符：{'、'.join(long_skills[:3])}",
                    row=row_number,
                    record_id=record.id,
                )

        if record.source_url.strip():
            source_urls[record.source_url.strip()] += 1

        if (
            "演示" in record.source
            or "虚构" in record.source
            or "example.com" in record.source_url
        ):
            demo_records += 1

    existing_count = 0
    if existing_ids:
        existing_count = sum(
            1 for _, record in valid_records if record.id in existing_ids
        )

    for field, count in missing_fields.items():
        if count:
            add_warning(f"必填字段「{field}」缺失或为空：{count} 条")

    if salary_missing:
        add_warning(f"薪资面议（两端为空）：{salary_missing} 条")
    if salary_single_bound:
        add_warning(f"只有单边薪资：{salary_single_bound} 条")
    for value in sorted(unknown_education):
        add_warning(
            f"未知学历值「{value}」：{unknown_education[value]} 条，导入后原样保留"
        )
    for value in sorted(unknown_experience):
        add_warning(
            f"未知经验值「{value}」：{unknown_experience[value]} 条，导入后原样保留"
        )

    duplicate_urls = [
        ValueCount(value=url, count=count)
        for url, count in source_urls.items()
        if count > 1
    ]
    duplicate_urls.sort(key=lambda item: (-item.count, item.value))
    for item in duplicate_urls:
        add_warning(f"来源链接重复（{item.count} 次）：{item.value}")

    if demo_records:
        add_warning(
            f"演示/虚构记录 {demo_records} 条；这些数据不能用于新闻结论"
        )
    if existing_count:
        add_warning(
            f"{existing_count} 条 id 已存在于数据库，导入时按 on_conflict 策略处理"
        )

    return ValidationReport(
        dataset_name=dataset_name,
        total_records=len(records),
        valid_records=len(valid_records),
        invalid_records=len(records) - len(valid_records),
        duplicate_ids=duplicate_ids,
        existing_in_database=existing_count,
        missing_fields=dict(missing_fields),
        salary_missing=salary_missing,
        salary_single_bound=salary_single_bound,
        salary_outliers=salary_outliers,
        unknown_education=_sorted_counts(unknown_education),
        unknown_experience=_sorted_counts(unknown_experience),
        empty_skills=empty_skills,
        over_limit_skills=over_limit_skills,
        duplicate_skill_entries=duplicate_skill_entries,
        duplicate_source_urls=duplicate_urls,
        demo_records=demo_records,
        errors=errors,
        warnings=warnings,
        warning_count=warning_count,
    )


__all__ = [
    "CANONICAL_EDUCATION",
    "CANONICAL_EXPERIENCE",
    "validate_dataset",
]
