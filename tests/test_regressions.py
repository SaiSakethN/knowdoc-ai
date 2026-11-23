from datetime import timedelta

from sqlalchemy import text

from knowdoc.db import session
from knowdoc.models import Job, Version, now
from knowdoc.parsing import parse
from knowdoc.worker import claim


def test_chapter_overview_keeps_intro_and_toc():
    data = b'<html><body><div class="chapter"><h2>Indexes</h2><p>Indexes improve row retrieval.</p><div class="toc"><dl><dt><span class="sect1">11.1. Introduction</span></dt></dl></div></div></body></html>'
    sections, _ = parse(data, "html")
    assert any("Indexes improve row retrieval" in s.text for s in sections)
    assert any("11.1. Introduction" in s.text for s in sections)


def test_browser_origin_and_request_validation(client):
    response = client.post('/api/v1/collections', json={"name": "Browser"}, headers={"Origin": "http://127.0.0.1:5173"})
    assert response.status_code == 201
    response = client.post('/api/v1/collections', json={"name": "Cross origin"}, headers={"Origin": "https://external.example"})
    assert response.status_code == 403
    response = client.post('/api/v1/search', json={"question": "x", "top_k": 100})
    assert response.status_code == 422
    assert "x" not in response.json().get("error", "")


def test_last_expired_attempt_transitions_to_failed(client):
    collection = client.post('/api/v1/collections', json={"name": "Recovery"}).json()
    uploaded = client.post('/api/v1/documents', data={"collection_id": collection["id"]}, files={"file": ("r.md", b"# Recovery\nRetry limits are bounded.")}).json()
    with session() as db:
        job = db.get(Job, uploaded["job_id"])
        job.status, job.attempts, job.lease_until = "running", 3, now() - timedelta(seconds=1)
        db.commit()
    claim()
    with session() as db:
        assert db.get(Job, uploaded["job_id"]).status == "failed"
        assert db.get(Version, uploaded["version_id"]).status == "failed"
        assert db.scalar(text("SELECT current_schema()" )).startswith("test_")
