import json
from pathlib import Path

from scripts.verify_stats import compute_expected, load_records

SAMPLE_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "sample_jobs.json"


def test_pandas_recompute_matches_documented_demo_values() -> None:
    payload = json.loads(SAMPLE_PATH.read_text(encoding="utf-8-sig"))
    _, records, invalid, duplicates = load_records(payload)
    expected = compute_expected(records)

    assert invalid == 0
    assert duplicates == 0
    assert expected["overview"]["total_jobs"] == 10
    assert expected["overview"]["salary_available"] == 9
    assert expected["overview"]["salary_median"] == 12_500.0
    assert expected["overview"]["fresh_graduate_ratio"] == 0.8

    assert expected["education"]["breakdown"]["本科"]["count"] == 6
    assert expected["education"]["breakdown"]["硕士"]["count"] == 2
    assert sum(
        item["count"] for item in expected["education"]["breakdown"].values()
    ) == 10
    assert sum(
        item["count"] for item in expected["experience"]["breakdown"].values()
    ) == 10
    assert expected["skills"]["items"]["Git"]["count"] == 8
