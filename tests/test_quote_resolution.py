from knowdoc.answers import validate_claims


def test_whitespace_only_quote_resolution_returns_real_stored_offsets():
    stored = "GIN indexes are the preferred\n   text search index type."
    claims, valid = validate_claims({"claims": [{"text": "GIN is preferred.", "quote": "GIN indexes are the preferred text search index type.", "citation_ids": ["stored"]}]}, [{"id": "stored", "text": stored}])
    assert valid
    span = claims[0]["citation_spans"][0]
    assert stored[span["start"]:span["end"]] == span["quote"]
    assert claims[0]["quote"] == stored
    _, valid = validate_claims({"claims": [{"text": "Hash is preferred.", "quote": "Hash indexes are the preferred text search index type.", "citation_ids": ["stored"]}]}, [{"id": "stored", "text": stored}])
    assert not valid
