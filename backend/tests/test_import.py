import json

from fastapi.testclient import TestClient

from app.core import settings
from tests.conftest import import_payload, sample_payload


def test_import_valid_dataset(client: TestClient) -> None:
    response = import_payload(client, sample_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["total_records"] == 3
    assert body["imported"] == 3
    assert body["failed"] == 0


def test_import_creates_batch_record(client: TestClient) -> None:
    response = import_payload(client, sample_payload())
    assert response.status_code == 200

    body = response.json()
    assert body["batch_id"] is not None

    batches = client.get("/api/v1/imports/batches").json()
    assert len(batches) == 1
    assert batches[0]["id"] == body["batch_id"]
    assert batches[0]["source_file"] == "dataset.json"
    assert batches[0]["total_records"] == 3
    assert batches[0]["imported"] == 3
    assert batches[0]["failed"] == 0


def test_import_deduplicates_by_default(client: TestClient) -> None:
    import_payload(client, sample_payload())
    response = import_payload(client, sample_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["imported"] == 0
    assert body["skipped"] == 3


def test_import_update_existing_records(client: TestClient) -> None:
    import_payload(client, sample_payload())
    updated_payload = sample_payload()
    updated_payload["records"][0]["salary_max"] = 22000
    response = import_payload(client, updated_payload, on_conflict="update")
    assert response.status_code == 200
    assert response.json()["updated"] == 3

    job = client.get("/api/v1/jobs/job_t1").json()
    assert job["salary_max"] == 22000


def test_import_reports_bad_record_without_rejecting_file(
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
    response = import_payload(client, payload)
    assert response.status_code == 200
    body = response.json()
    assert body["imported"] == 3
    assert body["failed"] == 1
    assert body["errors"][0]["row"] == 4
    assert body["errors"][0]["record_id"] == "job_bad"


def test_import_rejects_duplicate_ids_within_file(client: TestClient) -> None:
    payload = sample_payload()
    payload["records"].append(dict(payload["records"][0]))
    body = import_payload(client, payload).json()
    assert body["imported"] == 3
    assert body["failed"] == 1
    assert "重复" in body["errors"][0]["message"]


def test_import_rejects_invalid_json(client: TestClient) -> None:
    response = client.post(
        "/api/v1/imports/json",
        files={"file": ("bad.json", "{not json", "application/json")},
    )
    assert response.status_code == 400


def test_import_rejects_non_json_extension(client: TestClient) -> None:
    response = client.post(
        "/api/v1/imports/json",
        files={"file": ("data.txt", json.dumps(sample_payload()), "text/plain")},
    )
    assert response.status_code == 400


def test_import_rejects_non_utf8(client: TestClient) -> None:
    response = client.post(
        "/api/v1/imports/json",
        files={"file": ("bad.json", b"\xff\xfe\x00", "application/json")},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "bad_request"


def test_import_rejects_oversized_file(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "max_upload_bytes", 10)
    response = import_payload(client, sample_payload())
    assert response.status_code == 413
    assert response.json()["code"] == "payload_too_large"


def test_import_reports_overlong_field(client: TestClient) -> None:
    payload = sample_payload()
    payload["records"].append(
        {
            "id": "job_long",
            "company": "长" * 201,
            "position": "超长字段岗位",
            "job_type": "测试开发",
            "city": "杭州",
            "education": "本科",
            "experience": "应届生",
            "skills": ["Python"],
        }
    )
    body = import_payload(client, payload).json()
    assert body["imported"] == 3
    assert body["failed"] == 1
    assert "company" in body["errors"][0]["message"]


def test_import_normalizes_education_and_experience(client: TestClient) -> None:
    payload = sample_payload()
    payload["records"] = [
        {
            "id": "job_norm",
            "company": "规范化公司",
            "position": "后端开发工程师",
            "job_type": "后端开发",
            "city": "杭州",
            "salary_min": 8000,
            "salary_max": 12000,
            "education": "大学本科",
            "experience": "应届毕业生",
            "is_fresh_graduate": False,
            "skills": ["java", "Java", " MySQL "],
            "collected_at": "2026-11-01",
        }
    ]
    response = import_payload(client, payload)
    assert response.status_code == 200

    job = client.get("/api/v1/jobs/job_norm").json()
    assert job["education"] == "本科"
    assert job["experience"] == "应届生"
    assert job["is_fresh_graduate"] is True
    assert job["skills"] == ["java", "MySQL"]
