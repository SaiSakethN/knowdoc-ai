def test_openapi_defines_search_answer_and_citation_outputs(client):
    document = client.get('/openapi.json').json()
    definitions = document['components']['schemas']
    assert {'AnswerOutput', 'PassageOutput', 'ClaimOutput', 'ConflictOutput', 'CitationSpan'} <= definitions.keys()
    answer = document['paths']['/api/v1/answers']['post']
    assert answer['responses']['200']['content']['application/json']['schema']['$ref'].endswith('/AnswerOutput')
    assert 'conflicting_evidence' in definitions['AnswerOutput']['properties']['status']['enum']
