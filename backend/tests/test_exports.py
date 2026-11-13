from fastapi.testclient import TestClient


def test_export_jobs_csv(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/exports/jobs.csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "joblens_jobs.csv" in response.headers["content-disposition"]

    text = response.content.decode("utf-8-sig")
    lines = text.strip().splitlines()
    assert lines[0].startswith("id,company,position,job_type")
    assert len(lines) == 4
    assert "job_t1" in text
    assert "Java; MySQL" in text


def test_export_jobs_csv_respects_filters(seeded_client: TestClient) -> None:
    response = seeded_client.get(
        "/api/v1/exports/jobs.csv", params={"education": "本科"}
    )
    assert response.status_code == 200
    lines = response.content.decode("utf-8-sig").strip().splitlines()
    assert len(lines) == 2
    assert "job_t1" in lines[1]
    assert "job_t2" not in lines[1]
