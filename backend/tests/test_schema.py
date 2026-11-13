from sqlalchemy import inspect
from sqlalchemy.orm import Session


def test_composite_indexes_created(db_session: Session) -> None:
    indexes = {
        item["name"]
        for item in inspect(db_session.get_bind()).get_indexes("job_postings")
    }
    assert {
        "ix_job_postings_job_type_education",
        "ix_job_postings_city_job_type",
        "ix_job_postings_experience_education",
    } <= indexes
