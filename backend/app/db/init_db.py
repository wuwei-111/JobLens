"""Create database tables.

Called on application startup as well as by CLI scripts. Keeping table
creation here (instead of at import time) makes tests and scripts predictable.
"""

from app.db.base import Base
from app.db.session import engine


def init_db() -> None:
    # Import models so they are registered on Base.metadata before create_all.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


__all__ = ["init_db"]
