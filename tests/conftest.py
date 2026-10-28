import pytest
from fastapi.testclient import TestClient

from app.database.connection import get_db
from app.main import app


def fake_db():
    """A fake database session. These tests never touch the real database."""
    yield None


@pytest.fixture()
def client():
    app.dependency_overrides[get_db] = fake_db
    yield TestClient(app)   # no "with", so the startup code is skipped
    app.dependency_overrides.clear()