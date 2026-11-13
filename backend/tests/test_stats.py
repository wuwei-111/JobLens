from fastapi.testclient import TestClient

from tests.conftest import import_payload, sample_payload


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

    by_category = {item["category"]: item["count"] for item in body["categories"]}
    assert by_category["编程语言"] == 3
    assert by_category["数据库"] == 2
    assert by_category["测试"] == 1


def test_skills_stats_respects_filters(seeded_client: TestClient) -> None:
    body = seeded_client.get(
        "/api/v1/stats/skills", params={"job_type": "测试开发"}
    ).json()
    assert body["total_jobs"] == 1
    assert {item["skill"] for item in body["items"]} == {"Python", "自动化测试"}


def test_quality_stats(seeded_client: TestClient) -> None:
    body = seeded_client.get("/api/v1/stats/quality").json()
    assert body["total_jobs"] == 3
    assert body["salary_available"] == 2
    assert body["salary_missing"] == 1
    assert body["salary_single_bound"] == 0
    assert body["salary_invalid_range"] == 0
    assert body["salary_outliers"] == 0
    assert body["unknown_education"] == []
    assert body["unknown_experience"] == []
    assert body["jobs_without_skills"] == 0
    assert body["duplicate_source_urls"] == []
    assert body["demo_records"] == 3  # test URLs point at example.com
    assert body["total_companies"] == 3
    assert body["total_cities"] == 1
    assert body["collected_from"] == "2026-11-01"
    assert body["collected_to"] == "2026-11-01"


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


def test_cross_stats(seeded_client: TestClient) -> None:
    body = seeded_client.get(
        "/api/v1/stats/cross",
        params={"row": "job_type", "column": "education"},
    ).json()
    assert body["row_dimension"] == "job_type"
    assert body["column_dimension"] == "education"
    assert body["total"] == 3

    groups = {group["group"]: group for group in body["groups"]}
    assert groups["后端开发"]["total"] == 2
    assert {
        item["name"]: item["count"]
        for item in groups["后端开发"]["distribution"]
    } == {"本科": 1, "硕士": 1}
    assert {
        item["name"]: item["count"]
        for item in groups["测试开发"]["distribution"]
    } == {"不限": 1}


def test_cross_stats_respects_filters(seeded_client: TestClient) -> None:
    body = seeded_client.get(
        "/api/v1/stats/cross",
        params={
            "row": "job_type",
            "column": "experience",
            "job_type": "后端开发",
        },
    ).json()
    assert body["total"] == 2
    assert len(body["groups"]) == 1
    assert {
        item["name"]: item["count"]
        for item in body["groups"][0]["distribution"]
    } == {"应届生": 1, "1-3年": 1}


def test_cross_stats_rejects_unknown_dimension(seeded_client: TestClient) -> None:
    response = seeded_client.get(
        "/api/v1/stats/cross", params={"row": "foo", "column": "education"}
    )
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_stats_filter_no_results(seeded_client: TestClient) -> None:
    body = seeded_client.get(
        "/api/v1/stats/education", params={"job_type": "不存在"}
    ).json()
    assert body["total"] == 0
    assert body["breakdown"] == []
    assert body["by_job_type"] == []


def test_all_salary_missing(client: TestClient) -> None:
    payload = sample_payload()
    for record in payload["records"]:
        record["salary_min"] = None
        record["salary_max"] = None
    import_payload(client, payload)

    body = client.get("/api/v1/stats/salary").json()
    assert body["total_jobs"] == 3
    assert body["salary_available"] == 0
    assert body["overall"]["count"] == 0
    assert body["overall"]["avg"] is None
    assert all(item["count"] == 0 for item in body["distribution"])


def test_unknown_education_and_unknown_skill_category(client: TestClient) -> None:
    payload = sample_payload()
    payload["records"][0]["education"] = "MBA"
    payload["records"][0]["skills"] = ["COBOL"]
    import_payload(client, payload)

    education = client.get("/api/v1/stats/education").json()
    assert {"name": "MBA", "count": 1, "ratio": round(1 / 3, 4)} in education[
        "breakdown"
    ]

    quality = client.get("/api/v1/stats/quality").json()
    assert {"value": "MBA", "count": 1} in quality["unknown_education"]

    skills = client.get("/api/v1/stats/skills").json()
    cobol = next(item for item in skills["items"] if item["skill"] == "COBOL")
    assert cobol["category"] == "其他"
    assert any(item["category"] == "其他" for item in skills["categories"])


def test_quality_flags_empty_skills_and_duplicate_urls(client: TestClient) -> None:
    payload = sample_payload()
    payload["records"][0]["skills"] = []
    payload["records"][1]["source_url"] = payload["records"][0]["source_url"]
    import_payload(client, payload)

    body = client.get("/api/v1/stats/quality").json()
    assert body["jobs_without_skills"] == 1
    assert body["duplicate_source_urls"] == [
        {"value": "https://example.com/1", "count": 2}
    ]


def test_stats_dont_divide_by_zero_on_empty_db(client: TestClient) -> None:
    overview = client.get("/api/v1/stats/overview").json()
    assert overview["total_jobs"] == 0
    assert overview["salary_avg"] is None
    assert overview["fresh_graduate_ratio"] == 0.0

    salary = client.get("/api/v1/stats/salary").json()
    assert salary["overall"]["count"] == 0
    assert all(item["count"] == 0 for item in salary["distribution"])
