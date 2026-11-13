from fastapi.testclient import TestClient


def test_overview(seeded_client: TestClient) -> None:
    body = seeded_client.get("/api/v1/stats/overview").json()
    assert body["total_jobs"] == 3
    assert body["total_companies"] == 3
    assert body["fresh_graduate_count"] == 2
    assert body["fresh_graduate_ratio"] == round(2 / 3, 4)
    assert body["salary_available"] == 2
    # Midpoints: 15000 and 20000 -> average 17500
    assert body["salary_avg"] == 17500.0
    assert body["salary_median"] == 17500.0


def test_education_stats(seeded_client: TestClient) -> None:
    body = seeded_client.get("/api/v1/stats/education").json()
    assert body["total"] == 3
    by_name = {item["name"]: item for item in body["breakdown"]}
    assert by_name["本科"]["count"] == 1
    assert by_name["本科"]["ratio"] == round(1 / 3, 4)
    assert len(body["by_job_type"]) == 2


def test_experience_stats(seeded_client: TestClient) -> None:
    body = seeded_client.get("/api/v1/stats/experience").json()
    assert body["total"] == 3
    assert body["fresh_graduate"]["count"] == 2
    by_name = {item["name"]: item["count"] for item in body["breakdown"]}
    assert by_name["应届生"] == 1
    assert by_name["不限"] == 1
    assert by_name["1-3年"] == 1


def test_skills_stats(seeded_client: TestClient) -> None:
    body = seeded_client.get("/api/v1/stats/skills").json()
    assert body["total_jobs"] == 3
    assert body["total_skills"] == 5
    by_name = {item["skill"]: item for item in body["items"]}
    assert by_name["MySQL"]["count"] == 2
    assert by_name["MySQL"]["ratio"] == round(2 / 3, 4)
    assert by_name["MySQL"]["category"] == "数据库"
    assert len(body["by_job_type"]) == 2


def test_skills_stats_respects_filters(seeded_client: TestClient) -> None:
    body = seeded_client.get(
        "/api/v1/stats/skills", params={"job_type": "测试开发"}
    ).json()
    assert body["total_jobs"] == 1
    assert {item["skill"] for item in body["items"]} == {"Python", "自动化测试"}


def test_salary_stats(seeded_client: TestClient) -> None:
    body = seeded_client.get("/api/v1/stats/salary").json()
    assert body["total_jobs"] == 3
    assert body["salary_available"] == 2
    assert body["overall"]["count"] == 2
    assert body["overall"]["avg"] == 17500.0
    assert body["overall"]["median"] == 17500.0
    assert sum(item["count"] for item in body["distribution"]) == 2
    assert len(body["by_job_type"]) == 1  # only 后端开发 has valid salary
    assert body["by_job_type"][0]["group"] == "后端开发"


def test_stats_dont_divide_by_zero_on_empty_db(client: TestClient) -> None:
    overview = client.get("/api/v1/stats/overview").json()
    assert overview["total_jobs"] == 0
    assert overview["salary_avg"] is None
    assert overview["fresh_graduate_ratio"] == 0.0

    salary = client.get("/api/v1/stats/salary").json()
    assert salary["overall"]["count"] == 0
    assert all(item["count"] == 0 for item in salary["distribution"])
