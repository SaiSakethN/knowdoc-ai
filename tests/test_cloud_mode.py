from sqlalchemy import select

from knowdoc.config import settings
from knowdoc.db import session
from knowdoc.models import Chunk, SourceFile


def test_card_free_cloud_has_durable_private_sources_and_honest_search(client, monkeypatch):
    cfg = settings()
    for key, value in {'cloud_mode': True, 'source_storage': 'database',
                       'embedding_backend': 'disabled', 'generation_backend': 'disabled',
                       'max_upload_bytes': 3 * 1024 * 1024, 'max_chunks': 200}.items():
        monkeypatch.setattr(cfg, key, value)
    def no_provider(*args, **kwargs):
        raise AssertionError('Card-free mode must not call an AI provider')
    monkeypatch.setattr('knowdoc.worker.embed', no_provider)
    monkeypatch.setattr('knowdoc.retrieval.embed', no_provider)
    monkeypatch.setattr('knowdoc.answers.generate', no_provider)
    assert client.get('/api/v1/capabilities').json()['semantic_search'] is False
    collection = client.post('/api/v1/collections', json={'name': 'Cloud sources'}).json()
    content = b'# Resume\nMy name is Morgan Rivera.\nExample Labs | Data Engineer     Jan 2026 - Present\nPipelines process daily financial reports.'
    upload = client.post('/api/v1/documents', data={'collection_id': collection['id']},
                         files={'file': ('resume.md', content)}).json()
    with session() as db:
        assert db.get(SourceFile, upload['version_id']).content == content
        chunks = db.scalars(select(Chunk).where(Chunk.version_id == upload['version_id'])).all()
        assert chunks and all(c.embedding is None for c in chunks)
    result = client.post('/api/v1/answers', json={'question': 'what is his current company'}).json()
    assert result['answer'] == 'Example Labs.'
    assert result['answer_method'] == 'extractive'
    assert client.get('/api/v1/citations/' + result['citations'][0]['id']).status_code == 200
    fallback = client.post('/api/v1/answers', json={'question': 'What do pipelines process?'}).json()
    assert fallback['status'] == 'evidence_only'
    assert 'not enabled' in fallback['answer']
    assert client.get('/api/v1/versions/' + upload['version_id'] + '/original').content == content
    assert client.post('/api/v1/versions/' + upload['version_id'] + '/reindex').status_code == 202
    assert client.delete('/api/v1/documents/' + upload['document_id']).status_code == 204
    with session() as db:
        assert db.get(SourceFile, upload['version_id']) is None
