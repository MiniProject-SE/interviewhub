"""Module 3 — unit tests for the TF-IDF similarity index (white-box)."""
import pytest

from app.core.text import split_tags, tokenize
from app.modules.questions.recommender import Doc, TfidfIndex

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
