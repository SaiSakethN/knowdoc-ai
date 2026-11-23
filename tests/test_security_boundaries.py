import uuid

from fastapi.testclient import TestClient
from sqlalchemy import delete

from knowdoc.api import app
from knowdoc.db import session
from knowdoc.models import Grant
from knowdoc.worker import process_one


def test_private_text_never_reaches_reranker_or_generator(client, fake_embeddings, monkeypatch):
    collection = client.post('/api/v1/collections', json={"name": "Private"}).json()
    data = client.post('/api/v1/documents', data={"collection_id": collection["id"]}, files={"file": ('secret.md', b'# Secret GIN\nPrivate sentinel must not reach another principal. GIN indexes support search.')}).json()
    process_one()
    calls = []
    monkeypatch.setattr('knowdoc.retrieval.rerank', lambda q, passages: calls.extend(passages) or passages)
    monkeypatch.setattr('knowdoc.answers.generate', lambda q, passages: calls.extend(passages) or ({'status': 'insufficient_evidence', 'claims': []}, {}))
    with TestClient(app) as other:
        registered = other.post('/api/v1/sessions/register', json={"email": f'boundary-{uuid.uuid4().hex}@example.com', "password": "test-boundary-password"}).json()
        other.headers['X-CSRF-Token'] = registered['csrf_token']
        r = other.post('/api/v1/answers', json={"question": "private sentinel GIN", "method": "hybrid_rerank", "mode": "generate"})
        assert r.status_code == 200
        assert r.json()['status'] == 'insufficient_evidence'
        assert not calls
        assert other.get(f'/api/v1/versions/{data["version_id"]}/original').status_code == 404


def test_revocation_during_generation_is_rechecked(client, fake_embeddings, monkeypatch):
    collection = client.post('/api/v1/collections', json={"name": "Revoke"}).json()
    uploaded = client.post('/api/v1/documents', data={"collection_id": collection["id"]}, files={"file": ('r.md', b'# GIN\nGIN indexes support full text search.')}).json()
    process_one()
    with TestClient(app) as other:
        principal = other.post('/api/v1/sessions/register', json={"email": f'revoke-{uuid.uuid4().hex}@example.com', "password": "test-boundary-password"}).json()
        other.headers['X-CSRF-Token'] = principal['csrf_token']
        client.post(f'/api/v1/documents/{uploaded["document_id"]}/grants', json={"email": principal['user']['email']})

        def generate(question, passages):
            with session() as db:
                db.execute(delete(Grant).where(Grant.document_id == uploaded['document_id'], Grant.user_id == principal['user']['id']))
                db.commit()
            return {'status': 'answered', 'claims': [{'text': 'GIN supports search.', 'citation_ids': [passages[0]['id']], 'quote': 'GIN indexes support full text search.'}]}, {}
        monkeypatch.setattr('knowdoc.answers.generate', generate)
        response = other.post('/api/v1/answers', json={"question": "GIN indexes", "mode": "generate"})
        assert response.status_code == 409
        assert response.json()['error'] == 'permissions_changed_retry_question'


def test_upload_limits_and_original_attachment(client, fake_embeddings):
    collection = client.post('/api/v1/collections', json={"name": "Bounded"}).json()
    too_large = client.post('/api/v1/documents', content=b'x', headers={'Content-Length': str(30 * 1024 * 1024)})
    assert too_large.status_code == 413
    content = b'# Safe path\nGenerated storage paths ignore the uploaded filename.'
    uploaded = client.post('/api/v1/documents', data={"collection_id": collection['id']}, files={'file': ('../../escaped.md', content)}).json()
    original = client.get(f'/api/v1/versions/{uploaded["version_id"]}/original')
    assert original.status_code == 200
    assert original.content == content
    assert 'attachment;' in original.headers['content-disposition']
    assert '..' not in original.headers['content-disposition']


def test_chunked_body_limit_rejects_before_json_validation(client):
    chunks = iter([b'{"name":"', b'x' * 70_000, b'"}'])
    response = client.post('/api/v1/collections', content=chunks, headers={'Content-Type': 'application/json'})
    assert response.status_code == 413
    assert response.json()['error'] == 'request_body_too_large'
