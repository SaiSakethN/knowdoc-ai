import pytest

from knowdoc.evaluation import metrics


def test_recall_rr_and_ndcg_on_known_rankings():
    result = metrics(["irrelevant", "a", "b"], {"a", "b"})
    assert result["recall_at_5"] == 1
    assert result["mrr"] == .5
    assert result["ndcg_at_5"] == pytest.approx((1 / __import__('math').log2(3) + .5) / (1 + 1 / __import__('math').log2(3)))
    assert metrics(["x"], {"a"}) == {"recall_at_5": 0, "mrr": 0, "ndcg_at_5": 0}
