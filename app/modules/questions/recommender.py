"""Text-similarity engine for the question bank.

* ``TfidfIndex`` is a dependency-free TF-IDF + cosine-similarity index
  built over question text, tags and topic.
* It powers duplicate detection: when a student adds a question that is
  >= DUPLICATE_THRESHOLD similar to an existing one, we bump
  ``times_asked`` instead of storing a duplicate.

Sprint 2 will build the AI suggestion ranking on top of this index.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from app.core.text import split_tags, tokenize

DUPLICATE_THRESHOLD = 0.85


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
