from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from knowdoc.api import app
from knowdoc.db import session
from knowdoc.models import Job, Version, now
from knowdoc.worker import process_one


def upload(client, text=b"# Indexing\nGIN indexes are preferred for full text search. B-tree supports equality.", **extra):
    collection = client.post("/api/v1/collections", json={"name": "Engineering"}).json()
    response = client.post("/api/v1/documents", data={"collection_id": collection["id"], "label": "18.7", **extra},
                           files={"file": ("indexes.md", text, "text/markdown")})
    assert response.status_code == 202, response.text
    return response.json(), collection


def test_upload_search_answer_citation_and_delete(client, fake_embeddings):
    result, collection = upload(client)
    assert process_one()
    docs = client.get("/api/v1/documents").json()["items"]
    assert docs[0]["versions"][0]["status"] == "ready"
    for method in ("keyword", "dense", "hybrid"):
        response = client.post("/api/v1/search", json={"question": "GIN indexes", "method": method})
        assert response.status_code == 200, response.text
        assert response.json()["passages"]
    response = client.post("/api/v1/answers", json={"question": "GIN indexes", "mode": "evidence"})
    assert response.status_code == 200, response.text
    citation = response.json()["citations"][0]
    assert response.json()["status"] == "evidence_only"
    assert client.get(f'/api/v1/citations/{citation["id"]}').json()["version"] == "18.7"
    assert client.delete(f'/api/v1/documents/{result["document_id"]}').status_code == 204
    assert client.get(f'/api/v1/citations/{citation["id"]}').status_code == 404


def test_duplicate_version_filters_reindex_and_stable_citation(client, fake_embeddings):
    data, collection = upload(client)
    process_one()
    old = client.post("/api/v1/search", json={"question": "GIN", "method": "keyword"}).json()["passages"][0]
    dupe = client.post("/api/v1/documents", data={"collection_id": collection["id"]}, files={
        "file": ("again.md", b"# Indexing\nGIN indexes are preferred for full text search. B-tree supports equality.")})
    assert dupe.json()["duplicate"]
    new = client.post("/api/v1/documents", data={"collection_id": collection["id"], "document_id": data["document_id"], "label": "19.0"},
                      files={"file": ("new.md", b"# Indexing\nGIN indexes support text search in version nineteen.")})
    assert new.status_code == 202
    process_one()
    filtered = client.post("/api/v1/search", json={"question": "GIN", "method": "keyword", "version_ids": [data["version_id"]]}).json()
    assert all(p["version"] == "18.7" for p in filtered["passages"])
    assert client.post(f'/api/v1/versions/{data["version_id"]}/reindex').status_code == 202
    process_one()
    assert client.get(f'/api/v1/citations/{old["id"]}').status_code == 200


def test_access_isolation_grant_revocation_and_csrf(client, fake_embeddings):
    data, _ = upload(client)
    process_one()
    cid = client.post("/api/v1/search", json={"question": "GIN", "method": "keyword"}).json()["passages"][0]["id"]
    with TestClient(app) as other:
        r = other.post("/api/v1/sessions/register", json={"email": "other-" + data["document_id"] + "@example.com", "password": "another-local-password"})
        other.headers["X-CSRF-Token"] = r.json()["csrf_token"]
        assert other.get(f"/api/v1/citations/{cid}").status_code == 404
        assert other.get("/api/v1/documents").json()["items"] == []
        assert other.post("/api/v1/search", json={"question": "GIN", "method": "hybrid"}).json()["passages"] == []
        assert other.delete(f'/api/v1/documents/{data["document_id"]}').status_code == 404
        granted = client.post(f'/api/v1/documents/{data["document_id"]}/grants', json={"email": r.json()["user"]["email"]})
        assert granted.status_code == 201
        assert other.get(f"/api/v1/citations/{cid}").status_code == 200
        assert client.delete(f'/api/v1/documents/{data["document_id"]}/grants/{r.json()["user"]["id"]}').status_code == 204
        assert other.get(f"/api/v1/citations/{cid}").status_code == 404
    client.headers.pop("X-CSRF-Token")
    assert client.post("/api/v1/search", json={"question": "GIN"}).status_code == 403


def test_expired_job_recovery_and_failed_reindex_retains_index(client, fake_embeddings, monkeypatch):
    data, _ = upload(client)
    with session() as db:
        job = db.get(Job, data["job_id"])
        job.status, job.attempts, job.lease_until = "running", 1, now() - timedelta(seconds=1)
        db.commit()
    assert process_one()
    with session() as db:
        assert db.get(Job, data["job_id"]).attempts == 2
        active = db.get(Version, data["version_id"]).active_generation
    client.post(f'/api/v1/versions/{data["version_id"]}/reindex')
    monkeypatch.setattr("knowdoc.worker.embed", lambda _: (_ for _ in ()).throw(RuntimeError("failure")))
    process_one()
    with session() as db:
        assert db.get(Version, data["version_id"]).active_generation == active
        failed = db.scalar(select(Job).where(Job.version_id == data["version_id"], Job.status == "failed"))
        failed_id = failed.id
    assert client.post(f"/api/v1/jobs/{failed_id}/retry").status_code == 200
    assert client.post("/api/v1/search", json={"question": "GIN", "method": "keyword"}).json()["passages"]
