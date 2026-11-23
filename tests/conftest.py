"""Integration suite uses an isolated PostgreSQL schema, never truncates user data."""
import hashlib
import uuid

import numpy as np
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from knowdoc.config import settings
from knowdoc.db import engine


@pytest.fixture(scope="session", autouse=True)
def isolated_database(tmp_path_factory):
    cfg = settings()
    original_url = cfg.database_url
    original_admin_url = cfg.migration_database_url
    schema = "test_" + uuid.uuid4().hex
    admin_url = original_admin_url or original_url
    admin = create_engine(admin_url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    separator = "&" if "?" in admin_url else "?"
    cfg.database_url = admin_url + separator + f"options=-csearch_path%3D{schema},public"
    cfg.migration_database_url = cfg.database_url
    cfg.storage_dir = tmp_path_factory.mktemp("uploads")
    engine.cache_clear()
    command.upgrade(Config("alembic.ini"), "head")
    yield
    engine().dispose()
    engine.cache_clear()
    cfg.database_url = original_url
    cfg.migration_database_url = original_admin_url
    with admin.begin() as connection:
        connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
    admin.dispose()


@pytest.fixture
def fake_embeddings(monkeypatch):
    # Test fixture only, never a production retrieval baseline or claimed semantic model.
    def embeddings(texts, **kwargs):
        result = []
        for value in texts:
            vector = np.zeros(768)
            for word in value.lower().split():
                index = int(hashlib.sha256(word.encode()).hexdigest()[:8], 16) % 768
                vector[index] += 1
            vector /= max(np.linalg.norm(vector), 1)
            result.append(vector.tolist())
        return result
    monkeypatch.setattr("knowdoc.worker.embed", embeddings)
    monkeypatch.setattr("knowdoc.retrieval.embed", embeddings)
    return embeddings


@pytest.fixture
def client():
    from knowdoc.api import app, rate_windows
    rate_windows.clear()
    with TestClient(app) as c:
        email = f"test-{uuid.uuid4().hex}@example.com"
        r = c.post("/api/v1/sessions/register", json={"email": email, "password": "local-test-password"})
        assert r.status_code == 201, r.text
        c.headers["X-CSRF-Token"] = r.json()["csrf_token"]
        c.user_email = email
        yield c
        from knowdoc.db import session
        from knowdoc.models import User
        with session() as db:
            db.delete(db.get(User, r.json()["user"]["id"]))
            db.commit()
