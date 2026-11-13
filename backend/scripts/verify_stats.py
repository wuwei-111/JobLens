"""Independent statistics cross-check.

Recompute the four core indicator families from the raw JSON with Pandas, then
compare every value against the running FastAPI statistics endpoints. The
calculation here intentionally duplicates the bin boundaries and ordering rules
so a change in the API is caught instead of inherited.

Usage (run from ``backend/``, with the API running)::

    python -m scripts.verify_stats
    python -m scripts.verify_stats data/raw/hangzhou_graduate_jobs_2026-11-13_expanded.json --json > verify.json
    python -m scripts.verify_stats data/raw/a.json data/raw/b.json --json > verify.json
    python -m scripts.verify_stats --base-url http://127.0.0.1:8000/api/v1

With no paths it checks every real dataset under ``data/raw/``
(``*_graduate_jobs_*.json``) merged in filename order, matching the seed and
reset scripts. Duplicate ids across files are counted and skipped.

Exit codes: 0 = all checks pass, 1 = at least one mismatch, 2 = cannot load or
reach the data/API.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
from pydantic import ValidationError

from app.schemas.job import JobRecordIn
from app.services.importer import parse_dataset
from app.services.normalization import (
    normalize_education,
    normalize_experience,
    normalize_job_type,
    normalize_skills,
)
from app.services.skills import categorize_skill

DATA_RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
REAL_GLOB = "*_graduate_jobs_*.json"
SAMPLE_PATH = DATA_RAW / "sample_jobs.json"

# Deliberately duplicated from app.services.stats: the cross-check must notice
# if the API changes its bins or ordering.
SALARY_BINS: list[tuple[int | None, int | None, str]] = [
    (None, 8_000, "8K以下"),
    (8_000, 12_000, "8-12K"),
    (12_000, 16_000, "12-16K"),
    (16_000, 20_000, "16-20K"),
    (20_000, 30_000, "20-30K"),
    (30_000, None, "30K以上"),
]
EDUCATION_ORDER = [
    "不限",
    "大专",
    "本科",
    "本科及以上",
    "硕士",
    "硕士及以上",
    "博士",
    "其他",
    "未知",
]
EXPERIENCE_ORDER = [
    "不限",
    "应届生",
    "1年以内",
    "1-3年",
    "3-5年",
    "5年以上",
    "未披露",
    "其他",
    "未知",
]
SUMMARY_FIELDS = ("count", "avg", "median", "p25", "p75", "min", "max")
RATIO_TOLERANCE = 0.0001
MONEY_TOLERANCE = 0.02


def _ratio(count: int, total: int) -> float:
    return round(count / total, 4) if total else 0.0


def _money(value: float) -> float:
    return round(float(value), 2)


def _count_items(
    series: pd.Series, total: int, order: list[str]
) -> dict[str, dict[str, float | int]]:
    counts = series.fillna("未知").astype(str).value_counts()
    result = {
        str(name): {
            "count": int(count),
            "ratio": _ratio(int(count), total),
        }
        for name, count in counts.items()
    }
    position = {name: index for index, name in enumerate(order)}
    return dict(
        sorted(
            result.items(),
            key=lambda item: (
                position.get(item[0], len(order)),
                -item[1]["count"],
            ),
        )
    )


def _salary_summary(values: pd.Series) -> dict[str, float | int | None]:
    values = pd.to_numeric(values, errors="coerce").dropna()
    if values.empty:
        return {
            "count": 0,
            "avg": None,
            "median": None,
            "p25": None,
            "p75": None,
            "min": None,
            "max": None,
        }
    return {
        "count": int(values.size),
        "avg": _money(values.mean()),
        "median": _money(values.median()),
        "p25": _money(values.quantile(0.25)),
        "p75": _money(values.quantile(0.75)),
        "min": _money(values.min()),
        "max": _money(values.max()),
    }


def _salary_distribution(values: pd.Series) -> dict[str, dict[str, float | int]]:
    values = pd.to_numeric(values, errors="coerce").dropna()
    total = int(values.size)
    result: dict[str, dict[str, float | int]] = {}
    for lower, upper, label in SALARY_BINS:
        if lower is None:
            mask = values < upper
        elif upper is None:
            mask = values >= lower
        else:
            mask = (values >= lower) & (values < upper)
        count = int(mask.sum())
        result[label] = {"count": count, "ratio": _ratio(count, total)}
    return result


def _salary_groups(
    df: pd.DataFrame, column: str
) -> dict[str, dict[str, float | int | None]]:
    result: dict[str, dict[str, float | int | None]] = {}
    for group_name, group in df.groupby(column, dropna=False):
        summary = _salary_summary(group["salary_mid"])
        if summary["count"] == 0:
            continue
        result[str(group_name)] = summary
    return result


def _grouped_counts(
    df: pd.DataFrame, group_column: str, value_column: str, order: list[str]
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for group_name, group in df.groupby(group_column, dropna=False):
        total = len(group)
        distribution = _count_items(group[value_column], total, order)
        result[str(group_name)] = {
            "total": total,
            "distribution": {
                name: item["count"] for name, item in distribution.items()
            },
        }
    return result


def load_records(payload: Any) -> tuple[str, list[dict[str, Any]], int, int]:
    """Load valid, first-occurrence records using the import rules."""
    dataset_name, _, raw_records = parse_dataset(payload)
    seen: set[str] = set()
    records: list[dict[str, Any]] = []
    invalid = 0
    duplicates = 0

    for raw in raw_records:
        if not isinstance(raw, dict):
            invalid += 1
            continue
        try:
            record = JobRecordIn.model_validate(raw)
        except ValidationError:
            invalid += 1
            continue
        if record.id in seen:
            duplicates += 1
            continue
        seen.add(record.id)

        experience = normalize_experience(record.experience)
        records.append(
            {
                "id": record.id,
                "company": record.company,
                "position": record.position,
                "job_type": normalize_job_type(record.job_type),
                "city": record.city,
                "education": normalize_education(record.education),
                "experience": experience,
                "is_fresh_graduate": record.is_fresh_graduate
                or experience == "应届生",
                "salary_min": record.salary_min,
                "salary_max": record.salary_max,
                "skills": normalize_skills(record.skills),
                "source_url": record.source_url,
                "collected_at": record.collected_at.isoformat()
                if record.collected_at
                else None,
            }
        )

    return dataset_name, records, invalid, duplicates


def compute_expected(records: list[dict[str, Any]]) -> dict[str, Any]:
    columns = [
        "id",
        "company",
        "position",
        "job_type",
        "city",
        "education",
        "experience",
        "is_fresh_graduate",
        "salary_min",
        "salary_max",
        "skills",
        "source_url",
        "collected_at",
    ]
    df = pd.DataFrame(records, columns=columns)
    total = len(df)

    if total:
        salary = df[["salary_min", "salary_max"]].apply(
            pd.to_numeric, errors="coerce"
        )
        df["salary_mid"] = salary.mean(axis=1, skipna=True)
    else:
        df["salary_mid"] = pd.Series(dtype="float64")

    salary = _salary_summary(df["salary_mid"])
    fresh_count = int(df["is_fresh_graduate"].sum()) if total else 0
    collected = [
        value for value in df["collected_at"].tolist() if value is not None
    ] if total else []

    skill_rows = (
        df[["id", "job_type", "skills"]]
        .explode("skills")
        .dropna(subset=["skills"])
        if total
        else pd.DataFrame(columns=["id", "job_type", "skills"])
    )
    if not skill_rows.empty:
        skill_counts = skill_rows.groupby("skills")["id"].nunique()
        skill_counts = sorted(
            skill_counts.items(), key=lambda item: (-int(item[1]), item[0].casefold())
        )[:100]
        skill_items = {
            str(skill): {
                "count": int(count),
                "ratio": _ratio(int(count), total),
                "category": categorize_skill(str(skill)),
            }
            for skill, count in skill_counts
        }

        category_rows = skill_rows.copy()
        category_rows["category"] = category_rows["skills"].map(categorize_skill)
        category_counts = category_rows.groupby("category")["id"].nunique()
        categories = {
            str(category): {
                "count": int(count),
                "ratio": _ratio(int(count), total),
            }
            for category, count in sorted(
                category_counts.items(),
                key=lambda item: (-int(item[1]), item[0]),
            )
        }

        type_skill_counts: dict[str, dict[str, Any]] = {}
        for job_type, group in skill_rows.groupby("job_type"):
            counts = group.groupby("skills")["id"].nunique()
            ranked = sorted(
                counts.items(),
                key=lambda item: (-int(item[1]), item[0].casefold()),
            )[:50]
            type_total = int(df[df["job_type"] == job_type]["id"].nunique())
            type_skill_counts[str(job_type)] = {
                "total_jobs": type_total,
                "skills": {str(skill): int(count) for skill, count in ranked},
            }
        total_skills = int(skill_rows["skills"].nunique())
    else:
        skill_items = {}
        categories = {}
        type_skill_counts = {}
        total_skills = 0

    fresh_df = df[df["is_fresh_graduate"]] if total else df
    fresh_total = len(fresh_df)

    return {
        "dataset": {
            "valid_records": total,
            "invalid_records": None,  # filled by caller
            "duplicate_ids": None,
        },
        "overview": {
            "total_jobs": total,
            "total_companies": int(df["company"].nunique()) if total else 0,
            "total_cities": int(df["city"].nunique()) if total else 0,
            "total_job_types": int(df["job_type"].nunique()) if total else 0,
            "total_skills": total_skills,
            "salary_available": salary["count"],
            "salary_avg": salary["avg"],
            "salary_median": salary["median"],
            "fresh_graduate_count": fresh_count,
            "fresh_graduate_ratio": _ratio(fresh_count, total),
            "last_collected_at": max(collected) if collected else None,
        },
        "education": {
            "total": total,
            "breakdown": _count_items(df["education"], total, EDUCATION_ORDER),
            "by_job_type": _grouped_counts(
                df, "job_type", "education", EDUCATION_ORDER
            ),
        },
        "experience": {
            "total": total,
            "breakdown": _count_items(df["experience"], total, EXPERIENCE_ORDER),
            "by_job_type": _grouped_counts(
                df, "job_type", "experience", EXPERIENCE_ORDER
            ),
            "fresh_graduate": {
                "count": fresh_count,
                "ratio": _ratio(fresh_count, total),
                "breakdown": _count_items(
                    fresh_df["experience"], fresh_total, EXPERIENCE_ORDER
                ),
            },
        },
        "skills": {
            "total_jobs": total,
            "total_skills": total_skills,
            "items": skill_items,
            "categories": categories,
            "by_job_type": type_skill_counts,
        },
        "salary": {
            "total_jobs": total,
            "salary_available": salary["count"],
            "overall": salary,
            "distribution": _salary_distribution(df["salary_mid"]),
            "by_job_type": _salary_groups(df, "job_type"),
            "by_education": _salary_groups(df, "education"),
            "by_experience": _salary_groups(df, "experience"),
        },
    }


def fetch_api(base_url: str) -> dict[str, Any]:
    with httpx.Client(base_url=base_url, timeout=20) as client:
        education = client.get("/stats/education").raise_for_status().json()
        experience = client.get("/stats/experience").raise_for_status().json()
        skills = client.get(
            "/stats/skills", params={"limit": 100, "per_type_limit": 50}
        ).raise_for_status().json()
        salary = client.get("/stats/salary").raise_for_status().json()
        overview = client.get("/stats/overview").raise_for_status().json()
    return {
        "overview": overview,
        "education": education,
        "experience": experience,
        "skills": skills,
        "salary": salary,
    }


def _breakdown_map(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        item["name"]: {"count": item["count"], "ratio": item["ratio"]}
        for item in items
    }


def _items_map(items: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        entry: dict[str, Any] = {
            "count": item["count"],
            "ratio": item["ratio"],
        }
        # The category map is keyed by the category itself; only skill items
        # carry a separate category label to compare.
        if key != "category" and "category" in item:
            entry["category"] = item["category"]
        result[item[key]] = entry
    return result


def _grouped_map(groups: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        group["group"]: {
            "total": group["total"],
            "distribution": {
                item["name"]: item["count"]
                for item in group["distribution"]
            },
        }
        for group in groups
    }


def _salary_group_map(groups: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        group["group"]: {
            field: group[field] for field in SUMMARY_FIELDS
        }
        for group in groups
    }


def _skill_group_map(groups: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        group["job_type"]: {
            "total_jobs": group["total_jobs"],
            "skills": {item["skill"]: item["count"] for item in group["skills"]},
        }
        for group in groups
    }


class Checker:
    def __init__(self, tolerance: float = MONEY_TOLERANCE) -> None:
        self.tolerance = tolerance
        self.checks: list[dict[str, Any]] = []

    def scalar(
        self, section: str, name: str, expected: Any, actual: Any, tolerance: float = 0.0
    ) -> None:
        passed = self._equal(expected, actual, tolerance)
        self.checks.append(
            {
                "section": section,
                "name": name,
                "expected": expected,
                "actual": actual,
                "passed": passed,
            }
        )

    def count_ratio_map(
        self, section: str, expected: dict[str, dict[str, Any]], actual: dict[str, dict[str, Any]]
    ) -> None:
        for key in sorted(set(expected) | set(actual)):
            self.scalar(f"{section}.{key}", "count", expected.get(key, {}).get("count"), actual.get(key, {}).get("count"))
            self.scalar(
                f"{section}.{key}",
                "ratio",
                expected.get(key, {}).get("ratio"),
                actual.get(key, {}).get("ratio"),
                RATIO_TOLERANCE,
            )
            if "category" in expected.get(key, {}) or "category" in actual.get(key, {}):
                self.scalar(
                    f"{section}.{key}",
                    "category",
                    expected.get(key, {}).get("category"),
                    actual.get(key, {}).get("category"),
                )

    def grouped_map(
        self, section: str, expected: dict[str, dict[str, Any]], actual: dict[str, dict[str, Any]]
    ) -> None:
        for group in sorted(set(expected) | set(actual)):
            self.scalar(f"{section}.{group}", "total", expected.get(group, {}).get("total"), actual.get(group, {}).get("total"))
            expected_dist = expected.get(group, {}).get("distribution", {})
            actual_dist = actual.get(group, {}).get("distribution", {})
            for name in sorted(set(expected_dist) | set(actual_dist)):
                self.scalar(
                    f"{section}.{group}.{name}",
                    "count",
                    expected_dist.get(name),
                    actual_dist.get(name),
                )

    def skill_group_map(
        self, section: str, expected: dict[str, dict[str, Any]], actual: dict[str, dict[str, Any]]
    ) -> None:
        for group in sorted(set(expected) | set(actual)):
            self.scalar(f"{section}.{group}", "total_jobs", expected.get(group, {}).get("total_jobs"), actual.get(group, {}).get("total_jobs"))
            expected_skills = expected.get(group, {}).get("skills", {})
            actual_skills = actual.get(group, {}).get("skills", {})
            for skill in sorted(set(expected_skills) | set(actual_skills)):
                self.scalar(
                    f"{section}.{group}.{skill}",
                    "count",
                    expected_skills.get(skill),
                    actual_skills.get(skill),
                )

    def summary_map(
        self, section: str, expected: dict[str, dict[str, Any]], actual: dict[str, dict[str, Any]]
    ) -> None:
        for group in sorted(set(expected) | set(actual)):
            for field in SUMMARY_FIELDS:
                self.scalar(
                    f"{section}.{group}",
                    field,
                    expected.get(group, {}).get(field),
                    actual.get(group, {}).get(field),
                    MONEY_TOLERANCE if field != "count" else 0.0,
                )

    @staticmethod
    def _equal(expected: Any, actual: Any, tolerance: float) -> bool:
        if expected is None or actual is None:
            return expected is None and actual is None
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            return math.isclose(
                float(expected), float(actual), rel_tol=0.0, abs_tol=tolerance
            )
        return expected == actual


def compare(expected: dict[str, Any], api: dict[str, Any]) -> Checker:
    checker = Checker()

    for field, value in expected["overview"].items():
        checker.scalar(
            "overview",
            field,
            value,
            api["overview"].get(field),
            MONEY_TOLERANCE
            if field in {"salary_avg", "salary_median"}
            else RATIO_TOLERANCE
            if field == "fresh_graduate_ratio"
            else 0.0,
        )

    edu = expected["education"]
    checker.scalar("education", "total", edu["total"], api["education"].get("total"))
    checker.count_ratio_map("education.breakdown", edu["breakdown"], _breakdown_map(api["education"]["breakdown"]))
    checker.grouped_map("education.by_job_type", edu["by_job_type"], _grouped_map(api["education"]["by_job_type"]))

    exp = expected["experience"]
    checker.scalar("experience", "total", exp["total"], api["experience"].get("total"))
    checker.count_ratio_map("experience.breakdown", exp["breakdown"], _breakdown_map(api["experience"]["breakdown"]))
    checker.grouped_map("experience.by_job_type", exp["by_job_type"], _grouped_map(api["experience"]["by_job_type"]))
    checker.scalar("experience.fresh_graduate", "count", exp["fresh_graduate"]["count"], api["experience"]["fresh_graduate"].get("count"))
    checker.scalar("experience.fresh_graduate", "ratio", exp["fresh_graduate"]["ratio"], api["experience"]["fresh_graduate"].get("ratio"), RATIO_TOLERANCE)
    checker.count_ratio_map("experience.fresh_graduate.breakdown", exp["fresh_graduate"]["breakdown"], _breakdown_map(api["experience"]["fresh_graduate"]["breakdown"]))

    skills = expected["skills"]
    checker.scalar("skills", "total_jobs", skills["total_jobs"], api["skills"].get("total_jobs"))
    checker.scalar("skills", "total_skills", skills["total_skills"], api["skills"].get("total_skills"))
    checker.count_ratio_map("skills.items", skills["items"], _items_map(api["skills"]["items"], "skill"))
    checker.count_ratio_map("skills.categories", skills["categories"], _items_map(api["skills"]["categories"], "category"))
    checker.skill_group_map("skills.by_job_type", skills["by_job_type"], _skill_group_map(api["skills"]["by_job_type"]))

    salary = expected["salary"]
    checker.scalar("salary", "total_jobs", salary["total_jobs"], api["salary"].get("total_jobs"))
    checker.scalar("salary", "salary_available", salary["salary_available"], api["salary"].get("salary_available"))
    for field in SUMMARY_FIELDS:
        checker.scalar(
            "salary.overall",
            field,
            salary["overall"][field],
            api["salary"]["overall"].get(field),
            MONEY_TOLERANCE if field != "count" else 0.0,
        )
    checker.count_ratio_map("salary.distribution", salary["distribution"], _items_map(api["salary"]["distribution"], "label"))
    checker.summary_map("salary.by_job_type", salary["by_job_type"], _salary_group_map(api["salary"]["by_job_type"]))
    checker.summary_map("salary.by_education", salary["by_education"], _salary_group_map(api["salary"]["by_education"]))
    checker.summary_map("salary.by_experience", salary["by_experience"], _salary_group_map(api["salary"]["by_experience"]))

    return checker


def main() -> None:
    parser = argparse.ArgumentParser(description="JobLens 统计口径交叉核对")
    parser.add_argument(
        "paths",
        nargs="*",
        help=(
            "原始 JSON 数据集路径，可传多个；默认合并 data/raw/ 下全部 "
            "*_graduate_jobs_*.json，没有真实数据时使用演示数据"
        ),
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000/api/v1",
        help="FastAPI 基址（须已启动并已导入同一数据集）",
    )
    parser.add_argument("--json", action="store_true", help="输出完整 JSON 报告")
    parser.add_argument("--verbose", action="store_true", help="打印每一条检查")
    args = parser.parse_args()

    file_paths = [Path(item) for item in args.paths]
    if not file_paths:
        file_paths = sorted(DATA_RAW.glob(REAL_GLOB)) or [SAMPLE_PATH]
    for file_path in file_paths:
        if not file_path.is_file():
            raise SystemExit(f"文件不存在：{file_path}")

    dataset_names: list[str] = []
    records: list[dict[str, Any]] = []
    invalid = duplicates = 0
    seen_ids: set[str] = set()
    for file_path in file_paths:
        payload = json.loads(file_path.read_text(encoding="utf-8-sig"))
        try:
            dataset_name, file_records, file_invalid, file_duplicates = load_records(
                payload
            )
        except ValueError as exc:
            raise SystemExit(f"数据集结构错误（{file_path}）：{exc}") from exc
        dataset_names.append(dataset_name or file_path.name)
        invalid += file_invalid
        duplicates += file_duplicates
        for record in file_records:
            if record["id"] in seen_ids:
                duplicates += 1
                continue
            seen_ids.add(record["id"])
            records.append(record)

    expected = compute_expected(records)
    expected["dataset"] = {
        "valid_records": len(records),
        "invalid_records": invalid,
        "duplicate_ids": duplicates,
    }

    try:
        api = fetch_api(args.base_url.rstrip("/"))
    except httpx.HTTPError as exc:
        raise SystemExit(
            f"无法访问 API（{args.base_url}）：{exc}\n请先启动后端并导入同一数据集。"
        ) from exc

    checker = compare(expected, api)
    total = len(checker.checks)
    passed = sum(1 for check in checker.checks if check["passed"])
    failed = total - passed
    dataset_label = " / ".join(dataset_names)

    if args.json:
        report = {
            "dataset_name": dataset_label,
            "source_files": [str(file_path) for file_path in file_paths],
            "api": args.base_url,
            "dataset": expected["dataset"],
            "summary": {"total": total, "passed": passed, "failed": failed},
            "checks": checker.checks,
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"数据集：{dataset_label}")
        print(f"API：{args.base_url}")
        print(
            f"JSON：{len(records)} 条有效记录｜不可导入 {invalid}｜重复 id {duplicates}"
        )
        sections = sorted({check["section"].split(".")[0] for check in checker.checks})
        for section in sections:
            section_checks = [
                check for check in checker.checks if check["section"].split(".")[0] == section
            ]
            section_passed = sum(1 for check in section_checks if check["passed"])
            print(f"  {section}: {section_passed}/{len(section_checks)}")
        if args.verbose:
            for check in checker.checks:
                if check["passed"]:
                    print(
                        f"[PASS] {check['section']}.{check['name']}: "
                        f"{check['expected']} == {check['actual']}"
                    )
        for check in checker.checks:
            if not check["passed"]:
                print(
                    f"[FAIL] {check['section']}.{check['name']}: "
                    f"JSON={check['expected']!r}｜API={check['actual']!r}"
                )
        print(f"\n结果：{passed}/{total} 通过，{failed} 失败")
        if failed == 0:
            print("全部一致：Pandas 独立重算结果与 API 返回一致。")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
