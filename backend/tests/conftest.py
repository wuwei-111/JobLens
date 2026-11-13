"""Test fixtures: in-memory SQLite + FastAPI TestClient."""

from __future__ import annotations

import json
from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(
        bind=engine, autoflush=False, expire_on_commit=False
    )
    session = testing_session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.clear()


def sample_payload() -> dict[str, Any]:
    """Three valid records covering the main statistics branches."""
    return {
        "dataset_name": "测试数据集",
        "version": "1.0",
        "collected_at": "2026-11-01",
        "records": [
            {
                "id": "job_t1",
                "company": "甲公司",
                "position": "Java开发工程师",
                "job_type": "后端开发",
                "city": "杭州",
                "salary_min": 10000,
                "salary_max": 20000,
                "education": "本科",
                "experience": "应届生",
                "is_fresh_graduate": True,
                "skills": ["Java", "MySQL"],
                "description": "后端开发",
                "source": "test",
                "source_url": "https://example.com/1",
                "collected_at": "2026-11-01",
            },
            {
                "id": "job_t2",
                "company": "乙公司",
                "position": "Python开发工程师",
                "job_type": "后端开发",
                "city": "杭州",
                "salary_min": 15000,
                "salary_max": 25000,
                "education": "硕士",
                "experience": "1-3年",
                "is_fresh_graduate": False,
                "skills": ["Python", "MySQL", "Redis"],
                "description": "数据服务",
                "source": "test",
                "source_url": "https://example.com/2",
                "collected_at": "2026-11-01",
            },
            {
                "id": "job_t3",
                "company": "丙公司",
                "position": "测试开发工程师",
                "job_type": "测试开发",
                "city": "杭州",
                "salary_min": None,
                "salary_max": None,
                "education": "不限",
                "experience": "不限",
                "is_fresh_graduate": True,
                "skills": ["Python", "自动化测试"],
                "description": "测试平台",
                "source": "test",
                "source_url": "https://example.com/3",
                "collected_at": "2026-11-01",
            },
        ],
    }


def import_payload(client: TestClient, payload: dict[str, Any], **params: str):
    return client.post(
        "/api/v1/imports/json",
        params=params,
        files={
            "file": (
                "dataset.json",
                json.dumps(payload, ensure_ascii=False),
                "application/json",
            )
        },
    )


@pytest.fixture()
def seeded_client(client: TestClient) -> TestClient:
    response = import_payload(client, sample_payload())
    assert response.status_code == 200, response.text
    return client
