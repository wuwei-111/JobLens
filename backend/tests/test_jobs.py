from fastapi.testclient import TestClient


def test_list_jobs_pagination_and_skills(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/jobs", params={"page_size": 2})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert len(body["items"]) == 2
    assert isinstance(body["items"][0]["skills"], list)


def test_filter_jobs_by_education(seeded_client: TestClient) -> None:
    body = seeded_client.get("/api/v1/jobs", params={"education": "本科"}).json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == "job_t1"


def test_filter_jobs_by_salary_overlap(seeded_client: TestClient) -> None:
    body = seeded_client.get(
        "/api/v1/jobs", params={"salary_min": 24000, "salary_max": 30000}
    ).json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == "job_t2"


def test_filter_jobs_by_skill(seeded_client: TestClient) -> None:
    body = seeded_client.get("/api/v1/jobs", params={"skill": "Redis"}).json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == "job_t2"


def test_search_jobs_by_keyword(seeded_client: TestClient) -> None:
    body = seeded_client.get("/api/v1/jobs", params={"q": "Python"}).json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == "job_t2"


def test_get_job_detail_and_404(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/jobs/job_t1")
    assert response.status_code == 200
    assert response.json()["company"] == "甲公司"

    missing = seeded_client.get("/api/v1/jobs/not_exists")
    assert missing.status_code == 404


def test_filter_meta(seeded_client: TestClient) -> None:
    body = seeded_client.get("/api/v1/meta/filters").json()
    assert set(body["job_types"]) == {"后端开发", "测试开发"}
    assert "本科" in body["educations"]
    assert "MySQL" in body["skills"]
