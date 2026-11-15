"""Module 3 — unit tests for the TF-IDF suggestion engine (white-box)."""
import pytest

from app.core.text import split_tags, tokenize
from app.modules.questions import recommender as rec
from app.modules.questions.recommender import Doc, Query, TfidfIndex, recommend

DOCS = [
    Doc(1, "Reverse a linked list", "dsa", "linked-list", "Amazon", "SDE Intern", 3),
    Doc(2, "Detect cycle in a graph with DFS", "dsa", "graph,dfs", "Google", "SDE", 1),
    Doc(3, "Explain ACID transactions", "dbms", "transactions", "Oracle", "Software Engineer", 1),
    Doc(4, "Process versus thread", "os", "process,thread", None, None, 1),
]


def test_tokenize_and_tags():
    assert tokenize("What is C++ and C#?") == ["c++", "c#"]
    assert tokenize("") == []
    assert split_tags(" A, b ,,") == ["a", "b"]
    assert split_tags(None) == []


def test_index_similarity_prefers_matching_doc():
    idx = TfidfIndex(DOCS)
    sims = idx.similarities("graph cycle")
    assert max(range(len(sims)), key=sims.__getitem__) == 1
    assert idx.idf("graph") > idx.idf("dsa")  # rarer term weighs more


def test_cosine_edge_cases():
    assert TfidfIndex.cosine({}, {"a": 1.0}) == 0.0
    assert TfidfIndex.cosine({"a": 1.0, "b": 0.0}, {"a": 1.0}) == pytest.approx(1.0)


def test_most_similar_empty_and_hit():
    assert TfidfIndex([]).most_similar("x") == (None, 0.0)
    doc, sim = TfidfIndex(DOCS).most_similar("reverse linked list")
    assert doc.id == 1 and sim > 0.5


def test_vectorize_stopwords_only():
    assert TfidfIndex(DOCS).vectorize("the and of") == {}


def test_recommend_company_and_role_boost():
    out = recommend(DOCS, Query(company="Amazon", role_title="SDE Intern", limit=4))
    assert out[0].doc.id == 1
    assert "asked at this company" in out[0].reason and "relevant to the role" in out[0].reason


def test_recommend_partial_role_match():
    out = recommend(DOCS, Query(role_title="Senior Software Engineer", limit=4))
    assert out[0].doc.id == 3


def test_recommend_topic_filter_and_exclude():
    out = recommend(DOCS, Query(topic="dsa", exclude_ids={1}, limit=5))
    assert [s.doc.id for s in out] == [2]


def test_recommend_weak_topic_boost():
    out = recommend(DOCS, Query(weak_topics=["OS"], limit=4))
    top = next(s for s in out if s.doc.id == 4)
    assert "weak topic" in top.reason
    base = next(s for s in recommend(DOCS, Query(limit=4)) if s.doc.id == 4)
    assert top.score > base.score


def test_recommend_empty_and_limit():
    assert recommend([], Query()) == []
    assert recommend(DOCS, Query(exclude_ids={1, 2, 3, 4})) == []
    assert len(recommend(DOCS, Query(limit=0))) == 1  # at least one


def test_scores_are_bounded_and_sorted():
    out = recommend(DOCS, Query(text="graph dfs cycle", company="Google", role_title="SDE",
                                topic="dsa", weak_topics=["dsa"], limit=10))
    assert all(0 <= s.score <= 1 for s in out)
    assert out == sorted(out, key=lambda s: (-s.score, s.doc.id))


def test_explain_default():
    signals = dict(similarity=0, company=0, role=0, topic=0, popularity=0.1, weak_topic=0)
    assert rec._explain(signals) == "general practice"


def test_weights_sum_to_one():
    assert sum(rec.WEIGHTS.values()) == pytest.approx(1.0)


def test_provider_is_pluggable():
    class Fake:
        def suggest(self, docs, query):
            return [rec.Scored(docs[0], 1.0, "fake")]

    original = rec.provider
    try:
        rec.provider = Fake()
        assert rec.provider.suggest(DOCS, Query())[0].reason == "fake"
    finally:
        rec.provider = original
    assert isinstance(rec.provider, rec.LocalTfidfProvider)


def test_nfr2_ranking_1000_questions_under_200ms():
    import random
    import time

    rnd = random.Random(42)
    words = "graph tree array heap stack process thread memory index join sql cache api tcp dns model".split()
    docs = [Doc(i, " ".join(rnd.choices(words, k=12)), rnd.choice(["dsa", "os", "dbms"]),
                ",".join(rnd.choices(words, k=2)), rnd.choice(["A", "B"]), "SDE", rnd.randint(1, 5))
            for i in range(1000)]
    start = time.perf_counter()
    out = recommend(docs, Query(text="graph heap tree", company="A", role_title="SDE", limit=10))
    assert len(out) == 10
    assert time.perf_counter() - start < 0.2
