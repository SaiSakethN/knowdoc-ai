from knowdoc.facts import extract_profile_fact, profile_intent
from knowdoc.schemas import AnswerInput

INTRO = b'# Self Introduction\nMy name is Morgan Rivera. I am a Data Engineer with five years of experience.\n\nCurrently, I am working at Example Labs, where I build data pipelines. Previously, I worked at Old Company as an Analyst.'


def test_profile_defaults_and_exact_extraction():
    assert AnswerInput(question='what is your name').mode == 'generate'
    assert profile_intent('what is your current role?') == 'current_role'
    assert profile_intent('What is the role of GIN indexes?') is None
    source = {'id': 'real', 'text': INTRO.decode()}
    assert extract_profile_fact('what is your name', [source])['answer'] == 'Morgan Rivera.'
    assert extract_profile_fact('what is your current role', [source])['answer'] == 'Data Engineer at Example Labs.'
    source['text'] = 'Previously, I worked at Old Company as an Analyst.'
    assert extract_profile_fact('what is your current role', [source]) is None


def test_different_people_require_scope_clarification():
    sources = [{'id': 'a', 'text': 'My name is Morgan Rivera.'}, {'id': 'b', 'text': 'My name is Taylor Chen.'}]
    assert extract_profile_fact('what is your name', sources)['status'] == 'clarification_required'


def test_current_company_from_resume():
    source = {'id': 'resume', 'text': 'EXPERIENCE\nExample Labs | Data Scientist, Gen AI       Jan 2026 - Present\nOld Company | Analyst    Feb 2022 - July 2024'}
    for question in ['what is your current company', 'where does he work', 'current company he work from resume document']:
        result = extract_profile_fact(question, [source])
        assert result['answer'] == 'Example Labs.'
        assert result['claims'][0]['quote'] in source['text']
    source['text'] = 'Old Company | Analyst    Feb 2022 - July 2024'
    assert extract_profile_fact('what is your current company', [source]) is None
    assert extract_profile_fact('what is your current company', [{'id': 'intro', 'text': INTRO.decode()}])['answer'] == 'Example Labs.'


def test_simple_profile_answers_are_short_cited_and_private(client, fake_embeddings, monkeypatch):
    from knowdoc.worker import process_one
    collection = client.post('/api/v1/collections', json={'name': 'Profile'}).json()
    result = client.post('/api/v1/documents', data={'collection_id': collection['id']}, files={'file': ('profile.md', INTRO)})
    assert result.status_code == 202
    process_one()
    # Exact supported facts should not need to send the document to a generator.
    def no_generation(*args):
        raise AssertionError('Unnecessary generation for explicit profile fact')
    monkeypatch.setattr('knowdoc.answers.generate', no_generation)
    for question, expected in [('what is your name', 'Morgan Rivera.'), ('what is your current role', 'Data Engineer at Example Labs.'), ('where does he work', 'Example Labs.')]:
        response = client.post('/api/v1/answers', json={'question': question})
        assert response.status_code == 200, response.text
        output = response.json()
        assert output['answer'] == expected
        assert output['answer_method'] == 'extractive'
        assert len(output['citations']) == 1
        resolved = client.get('/api/v1/citations/' + output['citations'][0]['id'])
        assert resolved.status_code == 200
        assert output['claims'][0]['quote'] in resolved.json()['text']
    evidence = client.post('/api/v1/answers', json={'question': 'what is your name', 'mode': 'evidence'}).json()
    assert evidence['status'] == 'evidence_only'
