from knowdoc import providers


def test_local_generation_aliases_resolve_only_known_ids(monkeypatch):
    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"response": '{"status":"answered","claims":[{"text":"safe","quote":"a stored statement","citation_ids":["E1","invented"]}]}',
                    "prompt_eval_count": 10, "eval_count": 20}
    seen = []

    def post(url, **kwargs):
        seen.append(kwargs['json'])
        return Response()
    monkeypatch.setattr(providers.httpx, 'post', post)
    candidate, usage = providers.generate('Question?', [{'id': 'stored-id', 'version': 'v1', 'text': 'a stored statement'}])
    assert candidate['claims'][0]['citation_ids'] == ['stored-id', 'invalid-model-citation']
    assert seen[0]['format']['properties']['claims']['items']['properties']['citation_ids']['items']['enum'] == ['E1']
    assert usage['api_cost_usd'] == 0
