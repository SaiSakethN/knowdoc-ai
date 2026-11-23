from knowdoc.answers import conflicts, validate_claims


def test_opposing_numeric_policies_preserve_both_quotes_and_versions():
    passages = [
        {"id": "a", "version": "v1", "text": "The retention period is 30 days."},
        {"id": "b", "version": "v2", "text": "The retention period is 90 days."},
    ]
    found = conflicts(passages)
    assert found[0]["citation_ids"] == ["a", "b"]
    assert found[0]["quotes"] == [p["text"] for p in passages]
    assert found[0]["versions"] == ["v1", "v2"]


def test_different_policy_scope_and_identical_values_are_not_conflicts():
    assert not conflicts([
        {"id": "a", "version": "v1", "text": "The retention period is 30 days."},
        {"id": "b", "version": "v2", "text": "The retention period is 30 days. The polling interval is 90 seconds."},
    ])
    assert validate_claims([], [])[1] is False
