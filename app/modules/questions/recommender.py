"""AI-based question suggestion engine.

Design
------
* ``TfidfIndex`` is a dependency-free TF-IDF + cosine-similarity index
  built over question text, tags and topic.
* ``recommend`` blends that content similarity with contextual signals:
    final = 0.55*similarity + 0.15*company + 0.10*role + 0.10*topic
            + 0.05*popularity + 0.05*weak_topic
  Each signal is in [0, 1], so the final score is in [0, 1].
* ``SuggestionProvider`` is a protocol: an LLM-backed provider can be
  plugged in later without touching callers (Open/Closed principle).

The same index powers duplicate detection: when a student adds a
question that is >= DUPLICATE_THRESHOLD similar to an existing one, we
bump ``times_asked`` instead of storing a duplicate.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Protocol

from app.core.text import split_tags, tokenize

DUPLICATE_THRESHOLD = 0.85

WEIGHTS = {
    "similarity": 0.55,
    "company": 0.15,
    "role": 0.10,
    "topic": 0.10,
    "popularity": 0.05,
    "weak_topic": 0.05,
}


@dataclass(frozen=True)
class Doc:
    """Minimal view of a question that the engine needs (decoupled from ORM)."""

    id: int
    text: str
    topic: str
    tags: str = ""
    company: str | None = None
    role_title: str | None = None
    times_asked: int = 1


@dataclass
class Query:
    text: str = ""
    company: str | None = None
    role_title: str | None = None
    topic: str | None = None
    weak_topics: list[str] = field(default_factory=list)
    exclude_ids: set[int] = field(default_factory=set)
    limit: int = 10


@dataclass(frozen=True)
class Scored:
    doc: Doc
    score: float
    reason: str


def doc_terms(doc: Doc, text_only: bool = False) -> list[str]:
    # Tags and topic are repeated so they weigh more than body words.
    if text_only:
        return tokenize(doc.text)
    tags = split_tags(doc.tags)
    return tokenize(doc.text) + tags * 2 + [doc.topic] * 2


class TfidfIndex:
    """TF-IDF index. ``text_only=True`` ignores tags/topic (used for duplicate detection,
    where a new question's text is compared against existing question texts)."""

    def __init__(self, docs: Iterable[Doc], text_only: bool = False):
        self.docs: list[Doc] = list(docs)
        self._df: Counter[str] = Counter()
        tfs: list[Counter[str]] = []
        for d in self.docs:
            tf = Counter(doc_terms(d, text_only))
            tfs.append(tf)
            self._df.update(tf.keys())
        self._n = len(self.docs)
        self._vectors = [self._weigh(tf) for tf in tfs]

    def idf(self, term: str) -> float:
        # Smoothed IDF, always > 0.
        return math.log((1 + self._n) / (1 + self._df.get(term, 0))) + 1.0

    def _weigh(self, tf: Counter[str]) -> dict[str, float]:
        vec = {t: (1 + math.log(c)) * self.idf(t) for t, c in tf.items()}
        norm = math.sqrt(sum(v * v for v in vec.values()))
        return {t: v / norm for t, v in vec.items()} if norm else {}

    def vectorize(self, text: str) -> dict[str, float]:
        return self._weigh(Counter(tokenize(text)))

    @staticmethod
    def cosine(a: dict[str, float], b: dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        if len(a) > len(b):
            a, b = b, a
        return sum(v * b.get(t, 0.0) for t, v in a.items())

    def similarities(self, text: str) -> list[float]:
        q = self.vectorize(text)
        return [self.cosine(q, v) for v in self._vectors]

    def most_similar(self, text: str) -> tuple[Doc | None, float]:
        if not self.docs:
            return None, 0.0
        sims = self.similarities(text)
        best = max(range(len(sims)), key=sims.__getitem__)
        return self.docs[best], sims[best]


def _eq(a: str | None, b: str | None) -> bool:
    return bool(a) and bool(b) and a.strip().lower() == b.strip().lower()


def _role_match(query_role: str | None, doc_role: str | None) -> float:
    if not query_role or not doc_role:
        return 0.0
    if _eq(query_role, doc_role):
        return 1.0
    q, d = set(tokenize(query_role)), set(tokenize(doc_role))
    return len(q & d) / len(q | d) if q and d else 0.0


def recommend(docs: list[Doc], query: Query) -> list[Scored]:
    candidates = [d for d in docs if d.id not in query.exclude_ids]
    if not candidates:
        return []
    index = TfidfIndex(candidates)
    has_text = bool(tokenize(query.text))
    sims = index.similarities(query.text) if has_text else [0.0] * len(candidates)
    max_pop = max(d.times_asked for d in candidates) or 1
    weak = {t.lower() for t in query.weak_topics}

    results: list[Scored] = []
    for doc, sim in zip(candidates, sims):
        signals = {
            "similarity": sim,
            "company": 1.0 if _eq(query.company, doc.company) else 0.0,
            "role": _role_match(query.role_title, doc.role_title),
            "topic": 1.0 if _eq(query.topic, doc.topic) else 0.0,
            "popularity": doc.times_asked / max_pop,
            "weak_topic": 1.0 if doc.topic.lower() in weak else 0.0,
        }
        # Hard filter: if the user asked for a topic, only that topic.
        if query.topic and not signals["topic"]:
            continue
        score = sum(WEIGHTS[k] * v for k, v in signals.items())
        results.append(Scored(doc, round(score, 4), _explain(signals)))

    results.sort(key=lambda s: (-s.score, s.doc.id))
    return results[: max(1, query.limit)]


def _explain(signals: dict[str, float]) -> str:
    parts = []
    if signals["similarity"] >= 0.2:
        parts.append("matches your search")
    if signals["company"]:
        parts.append("asked at this company")
    if signals["role"] >= 0.5:
        parts.append("relevant to the role")
    if signals["weak_topic"]:
        parts.append("targets a weak topic")
    if signals["popularity"] >= 0.75:
        parts.append("frequently asked")
    return ", ".join(parts) or "general practice"


class SuggestionProvider(Protocol):
    def suggest(self, docs: list[Doc], query: Query) -> list[Scored]: ...


class LocalTfidfProvider:
    """Default provider: offline, deterministic, no API keys required."""

    def suggest(self, docs: list[Doc], query: Query) -> list[Scored]:
        return recommend(docs, query)


provider: SuggestionProvider = LocalTfidfProvider()
