from knowdoc.db import session
from knowdoc.models import EvaluationTask
from knowdoc.worker import process_evaluation


def test_evaluation_queue_requires_corpus_and_scopes_runs(client, monkeypatch):
    assert client.post('/api/v1/evaluations').status_code == 409
    for name in ['PostgreSQL · versioned reference', 'Original evaluation fixtures']:
        assert client.post('/api/v1/collections', json={'name': name}).status_code == 201
    task = client.post('/api/v1/evaluations').json()
    duplicate = client.post('/api/v1/evaluations').json()
    assert task['task_id'] == duplicate['task_id']
    # A failure is persisted, without logging or returning a private exception body.
    monkeypatch.setattr('knowdoc.evaluation.run_evaluation', lambda *_: (_ for _ in ()).throw(ValueError('private failure text')))
    assert process_evaluation()
    with session() as db:
        result = db.get(EvaluationTask, task['task_id'])
        assert result.status == 'failed'
        assert result.error == 'ValueError'
    assert client.get('/api/v1/evaluations/missing').status_code == 404
