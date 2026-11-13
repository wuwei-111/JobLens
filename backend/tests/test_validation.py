import json
from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import import_payload, sample_payload


def validate_payload(client: TestClient, payload: dict[str, Any]):
    return client.post(
        "/api/v1/imports/validate",
        files={
            "file": (
                "dataset.json",
                json.dumps(payload, ensure_ascii=False),
                "application/json",
            )
        },
    )


def test_validate_reports_without_writing(client: TestClient) -> None:
    response = validate_payload(client, sample_payload())
    assert response.status_code == 200

    body = response.json()
    assert body["total_records"] == 3
    assert body["valid_records"] == 3
    assert body["invalid_records"] == 0
    assert body["salary_missing"] == 1
    assert body["demo_records"] == 3
    assert body["existing_in_database"] == 0

    # Preflight must not insert anything.
    assert client.get("/api/v1/stats/overview").json()["total_jobs"] == 0
    assert client.get("/api/v1/imports/batches").json() == []


def test_validate_reports_bad_rows_and_quality_warnings(
    client: TestClient,
) -> None:
    payload = sample_payload()
    payload["records"].append(
        {
            "id": "job_bad",
            "company": "丁公司",
            "position": "坏数据岗位",
            "salary_min": 20000,
            "salary_max": 10000,
        }
    )
    payload["records"].append(
        {
            "id": "job_unknown",
            "company": "戊公司",
            "position": "数据治理工程师",
            "job_type": "数据分析",
            "city": "杭州",
            "salary_min": 5000,
            "salary_max": 6000,
            "education": "MBA",
            "experience": "10年以上",
            "is_fresh_graduate": False,
            "skills": [],
            "description": "测试未知枚举与空技能",
            "source": "公开招聘",
            "source_url": "https://example.org/jobs/job_unknown",
            "collected_at": "2026-11-01",
        }
    )

    body = validate_payload(client, payload).json()
    assert body["total_records"] == 5
    assert body["valid_records"] == 4
    assert body["invalid_records"] == 1
    assert body["errors"][0]["row"] == 4
    assert body["errors"][0]["record_id"] == "job_bad"

    assert body["unknown_education"] == [{"value": "MBA", "count": 1}]
    assert body["unknown_experience"] == [{"value": "10年以上", "count": 1}]
    assert body["empty_skills"] == 1
    assert body["warning_count"] > 0


def test_validate_reports_duplicate_ids(client: TestClient) -> None:
    payload = sample_payload()
    payload["records"].append(dict(payload["records"][0]))

    body = validate_payload(client, payload).json()
    assert body["duplicate_ids"] == 1
    assert body["invalid_records"] == 1


def test_validate_reports_ids_already_in_database(client: TestClient) -> None:
    import_payload(client, sample_payload())

    body = validate_payload(client, sample_payload()).json()
    assert body["existing_in_database"] == 3
    assert any("已存在于数据库" in item["message"] for item in body["warnings"])
