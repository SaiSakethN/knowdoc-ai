def test_generic_question_adjectives_do_not_authorize_unrelated_generation(client, fake_embeddings, monkeypatch):
    from knowdoc.worker import process_one
    collection = client.post('/api/v1/collections', json={'name': 'Relevance'}).json()
    client.post('/api/v1/documents', data={'collection_id': collection['id']}, files={'file': ('indexes.md', b'# Ordering\nA B-tree is the best index for ordering table rows.')})
    process_one()
    calls = []

    def generate(question, passages):
        calls.append(question)
        return {'status': 'answered', 'claims': [{'text': 'B-tree supports ordering.', 'quote': 'A B-tree is the best index for ordering table rows.', 'citation_ids': [passages[0]['id']]}]}, {}
    monkeypatch.setattr('knowdoc.answers.generate', generate)
    unrelated = client.post('/api/v1/answers', json={'question': 'Which restaurant serves the best sushi in Boston?', 'mode': 'generate'})
    assert unrelated.json()['status'] == 'insufficient_evidence'
    assert not calls
    related = client.post('/api/v1/answers', json={'question': 'Which index supports ordering?', 'mode': 'generate'})
    assert related.json()['status'] == 'answered'
    assert len(calls) == 1
