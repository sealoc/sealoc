"""
Unit test for sealocs database package.
"""

from __future__ import annotations

import sqlalchemy as sqla
import sealoc.database as db

from pathlib import Path


def test_create_engine_with_explicit_url(tmp_path: Path) -> None:
    """Engine is created from the URL argument."""

    db_path: Path = tmp_path / "explicit.db"
    db_path.touch()
    url: str = f"sqlite:///{db_path}"

    engine: db.Engine = db.create_engine(url=url, verbose=False)

    assert isinstance(engine, db.Engine)
    with engine.connect() as conn:
        result = conn.execute(sqla.text("SELECT 1"))
        value: int = result.scalar_one()
        assert value == 1
