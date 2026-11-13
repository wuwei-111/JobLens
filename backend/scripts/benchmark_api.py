"""API performance benchmark on a temporary 500-record dataset.

The script never touches the main database: it generates synthetic records from
the demo dataset, imports them into a temporary SQLite file, and drives the
FastAPI app with TestClient. It prints median/p95 latency for the main
endpoints and exits non-zero if any endpoint exceeds the 300 ms target.

Usage (run from ``backend/``)::

    python -m scripts.benchmark_api
    python -m scripts.benchmark_api --count 500 --iterations 20 --json
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any

THRESHOLD_SECONDS = 0.300


def build_payload(source: dict[str, Any], count: int) -> dict[str, Any]:
    bases = source["records"]
    records: list[dict[str, Any]] = []
    for index in range(count):
        record = dict(bases[index % len(bases)])
        record["id"] = f"bench_{index:04d}"
        record["source"] = "基准测试（虚构）"
        record["source_url"] = f"https://example.com/bench/{index:04d}"
        record["collected_at"] = "2026-11-13"
        if record.get("salary_min") is not None:
            record["salary_min"] += (index % 5) * 500
        if record.get("salary_max") is not None:
            record["salary_max"] += (index % 5) * 500
        records.append(record)
    return {
        "dataset_name": f"性能基准数据（{count} 条，虚构）",
        "version": "benchmark",
        "collected_at": "2026-11-13",
        "records": records,
    }


def p95(values: list[float]) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(0.95 * len(ordered)) - 1)
    return ordered[index]


def main() -> None:
    parser = argparse.ArgumentParser(description="JobLens API 性能基准")
    parser.add_argument(
        "path",
        nargs="?",
        default="data/raw/sample_jobs.json",
        help="用于生成基准数据的原始 JSON",
    )
    parser.add_argument("--count", type=int, default=500, help="生成记录数")
    parser.add_argument("--iterations", type=int, default=20, help="每个接口计时次数")
    parser.add_argument("--json", action="store_true", help="输出 JSON 报告")
    args = parser.parse_args()

    source_path = Path(args.path)
    if not source_path.is_file():
        raise SystemExit(f"文件不存在：{source_path}")
    source = json.loads(source_path.read_text(encoding="utf-8-sig"))
    payload = build_payload(source, args.count)

    with tempfile.TemporaryDirectory(prefix="joblens-bench-") as tmp:
        db_path = Path(tmp) / "benchmark.db"
        os.environ["JOBLENS_DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"

        # Import the app only after the environment variable is set: settings
        # and the engine are created at import time.
        from app.db.init_db import init_db
        from app.db.session import SessionLocal, engine
        from app.main import app
        from app.services.importer import import_dataset
        from fastapi.testclient import TestClient

        init_db()
        with SessionLocal() as db:
            imported = import_dataset(db, payload, source_file="benchmark")

        endpoints = [
            ("overview", "/api/v1/stats/overview", {}),
            ("education", "/api/v1/stats/education", {}),
            ("experience", "/api/v1/stats/experience", {}),
            (
                "skills",
                "/api/v1/stats/skills",
                {"limit": 50, "per_type_limit": 10},
            ),
            ("salary", "/api/v1/stats/salary", {}),
            ("quality", "/api/v1/stats/quality", {}),
            (
                "cross",
                "/api/v1/stats/cross",
                {"row": "job_type", "column": "education"},
            ),
            ("jobs", "/api/v1/jobs", {"page_size": 20}),
            (
                "jobs_filtered",
                "/api/v1/jobs",
                {"job_type": "后端开发", "page_size": 20},
            ),
            ("meta", "/api/v1/meta/filters", {}),
            ("export_csv", "/api/v1/exports/jobs.csv", {}),
        ]

        results: list[dict[str, Any]] = []
        try:
            with TestClient(app) as client:
                overview = client.get("/api/v1/stats/overview")
                overview.raise_for_status()
                if overview.json()["total_jobs"] != args.count:
                    raise SystemExit(
                        f"基准数据未正确导入：期望 {args.count} 条，"
                        f"实际 {overview.json()['total_jobs']} 条"
                    )

                for name, path, params in endpoints:
                    for _ in range(3):
                        warm = client.get(path, params=params)
                        warm.raise_for_status()
                    times: list[float] = []
                    for _ in range(args.iterations):
                        started = time.perf_counter()
                        response = client.get(path, params=params)
                        times.append(time.perf_counter() - started)
                        response.raise_for_status()
                    results.append(
                        {
                            "endpoint": name,
                            "path": path,
                            "median_ms": round(statistics.median(times) * 1000, 1),
                            "p95_ms": round(p95(times) * 1000, 1),
                            "max_ms": round(max(times) * 1000, 1),
                            "ok": statistics.median(times) <= THRESHOLD_SECONDS
                            and p95(times) <= THRESHOLD_SECONDS,
                        }
                    )
        finally:
            engine.dispose()

        failed = [item for item in results if not item["ok"]]
        if args.json:
            print(
                json.dumps(
                    {
                        "records": args.count,
                        "iterations": args.iterations,
                        "threshold_ms": THRESHOLD_SECONDS * 1000,
                        "imported": imported.imported,
                        "results": results,
                        "failed": [item["endpoint"] for item in failed],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(
                f"临时数据库 · {args.count} 条记录 · 每接口 {args.iterations} 次 · "
                f"目标 < {THRESHOLD_SECONDS * 1000:.0f} ms"
            )
            print(f"{'接口':<16}{'median':>10}{'p95':>10}{'max':>10}  结果")
            for item in results:
                status = "PASS" if item["ok"] else "FAIL"
                print(
                    f"{item['endpoint']:<16}"
                    f"{item['median_ms']:>8.1f}ms"
                    f"{item['p95_ms']:>8.1f}ms"
                    f"{item['max_ms']:>8.1f}ms  {status}"
                )
            if failed:
                print("\n未达标：" + "、".join(item["endpoint"] for item in failed))
            else:
                print("\n全部接口 median 与 p95 均低于 300 ms。")

        if failed:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
