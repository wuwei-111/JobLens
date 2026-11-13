import json

from fastapi.testclient import TestClient

from tests.conftest import sample_payload


def test_not_found_error_envelope(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/jobs/not_exists")
    assert response.status_code == 404
    body = response.json()
    assert body["detail"] == "招聘记录不存在"
    assert body["code"] == "not_found"


def test_validation_error_envelope(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/jobs", params={"page": 0})
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert body["detail"] == "请求参数校验失败"
    assert body["errors"]


def test_bad_json_error_envelope(client: TestClient) -> None:
    response = client.post(
        "/api/v1/imports/json",
        files={"file": ("bad.json", "{not json", "application/json")},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "bad_request"
    assert "JSON" in body["detail"]


def test_validate_rejects_non_utf8(client: TestClient) -> None:
    response = client.post(
        "/api/v1/imports/validate",
        files={"file": ("bad.json", b"\xff\xfe\x00", "application/json")},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "bad_request"


def test_validate_rejects_non_json_extension(client: TestClient) -> None:
    response = client.post(
        "/api/v1/imports/validate",
        files={"file": ("data.txt", json.dumps(sample_payload()), "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "bad_request"
