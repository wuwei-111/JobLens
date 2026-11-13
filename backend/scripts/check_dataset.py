"""Offline JSON dataset checker.

Usage (run from ``backend/``)::

    python -m scripts.check_dataset
    python -m scripts.check_dataset data/raw/hangzhou_graduate_jobs_2026-11-13_expanded.json --json
    python -m scripts.check_dataset data/raw/jobs.json --strict

Exit codes: 0 = usable, 1 = invalid records (or warnings with --strict),
2 = the JSON structure itself is not a dataset.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.schemas.import_ import ImportErrorItem, ValidationReport
from app.services.validation import validate_dataset


def _print_issues(label: str, items: list[ImportErrorItem]) -> None:
    if not items:
        return
    print(f"\n{label}（{len(items)} 条展示）：")
    for item in items:
        location = []
        if item.row is not None:
            location.append(f"第 {item.row} 行")
        if item.record_id:
            location.append(item.record_id)
        prefix = f"[{' / '.join(location)}] " if location else ""
        print(f"  - {prefix}{item.message}")


def _print_report(report: ValidationReport) -> None:
    print(f"数据集：{report.dataset_name or '（未命名）'}")
    print(
        f"记录：{report.total_records} 条｜可导入 {report.valid_records}｜"
        f"不可导入 {report.invalid_records}｜文件内重复 id {report.duplicate_ids}"
    )
    if report.existing_in_database:
        print(f"数据库中已存在：{report.existing_in_database} 条")

    missing = {key: value for key, value in report.missing_fields.items() if value}
    print(
        "缺失字段："
        + ("无" if not missing else "，".join(f"{key} {value} 条" for key, value in missing.items()))
    )
    print(
        f"薪资：面议 {report.salary_missing}｜单边 {report.salary_single_bound}｜"
        f"疑似异常 {report.salary_outliers}"
    )
    print(
        "未知学历："
        + (
            "无"
            if not report.unknown_education
            else "，".join(f"{item.value} {item.count} 条" for item in report.unknown_education)
        )
    )
    print(
        "未知经验："
        + (
            "无"
            if not report.unknown_experience
            else "，".join(f"{item.value} {item.count} 条" for item in report.unknown_experience)
        )
    )
    print(
        f"技能：为空 {report.empty_skills}｜超过 10 项 {report.over_limit_skills}｜"
        f"重复 {report.duplicate_skill_entries}"
    )
    print(
        "重复来源链接："
        + (
            "无"
            if not report.duplicate_source_urls
            else "，".join(
                f"{item.value}（{item.count} 次）"
                for item in report.duplicate_source_urls[:5]
            )
        )
    )
    print(f"演示/虚构记录：{report.demo_records} 条")
    print(f"警告：{report.warning_count} 条")

    _print_issues("错误", report.errors)
    _print_issues("警告", report.warnings[:20])
    if report.warning_count > len(report.warnings[:20]):
        print(f"  … 其余 {report.warning_count - len(report.warnings[:20])} 条警告未展开")


def main() -> None:
    parser = argparse.ArgumentParser(description="离线检查 JobLens JSON 数据集")
    parser.add_argument(
        "path",
        nargs="?",
        default="data/raw/sample_jobs.json",
        help="JSON 文件路径（默认 data/raw/sample_jobs.json）",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出完整 JSON 报告，便于保存为交付材料",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="有任何警告也以退出码 1 结束",
    )
    args = parser.parse_args()

    file_path = Path(args.path)
    if not file_path.is_file():
        raise SystemExit(f"文件不存在：{file_path}")

    payload = json.loads(file_path.read_text(encoding="utf-8-sig"))
    try:
        report = validate_dataset(payload)
    except ValueError as exc:
        raise SystemExit(f"数据集结构错误：{exc}") from exc

    if args.json:
        print(report.model_dump_json(indent=2, ensure_ascii=False))
    else:
        _print_report(report)

    if report.invalid_records:
        raise SystemExit(1)
    if args.strict and report.warning_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
