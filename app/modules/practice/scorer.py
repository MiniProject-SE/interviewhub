"""Keyword-coverage answer scorer.

Pure functions with no DB access so they can be unit tested in isolation.

auto_score  = 100 * (0.75 * coverage + 0.25 * length_factor)
final_score = 0.7 * auto_score + 0.3 * (self_rating * 20)   (if self-rated)
"""
from collections import Counter
from dataclasses import dataclass

from app.core.text import split_tags, tokenize

MAX_KEYWORDS = 8
TARGET_WORDS = 40


@dataclass(frozen=True)
class ScoreResult:
    auto_score: float
    covered: list[str]
    missed: list[str]
    feedback: str


def extract_keywords(question_text: str, model_answer: str | None, tags: str | None) -> list[str]:
    """Key terms a good answer should mention, most important first."""
    keywords: list[str] = []
    stems: set[str] = set()

    def add(tok: str) -> None:
        if _stem(tok) not in stems:
            stems.add(_stem(tok))
            keywords.append(tok)

    for tag in split_tags(tags):
        for tok in tokenize(tag):
            add(tok)
    source = model_answer if model_answer else question_text
    for tok, _ in Counter(tokenize(source)).most_common():
        if len(keywords) >= MAX_KEYWORDS:
            break
        if len(tok) > 2:
            add(tok)
    return keywords[:MAX_KEYWORDS]


def _stem(token: str) -> str:
    """Tiny suffix stripper: threads->thread, processes->process (but process stays)."""
    if token.endswith("ss"):
        return token
    for suffix in ("sses", "ing", "ed", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            if suffix == "sses":
                return token[:-2]
            return token[: -len(suffix)]
    return token


def score_answer(answer: str, keywords: list[str]) -> ScoreResult:
    words = tokenize(answer)
    if not words:
        return ScoreResult(0.0, [], list(keywords), "No answer was given.")
    stems = {_stem(w) for w in words}
    covered = [k for k in keywords if _stem(k) in stems]
    missed = [k for k in keywords if k not in covered]
    coverage = len(covered) / len(keywords) if keywords else 1.0
    length_factor = min(1.0, len(answer.split()) / TARGET_WORDS)
    auto = round(100 * (0.75 * coverage + 0.25 * length_factor), 1)
    return ScoreResult(auto, covered, missed, build_feedback(auto, covered, missed, length_factor))


def build_feedback(score: float, covered: list[str], missed: list[str], length_factor: float) -> str:
    if score >= 80:
        verdict = "Strong answer."
    elif score >= 50:
        verdict = "Decent answer with gaps."
    else:
        verdict = "Needs work."
    parts = [verdict]
    if covered:
        parts.append("Covered: " + ", ".join(covered) + ".")
    if missed:
        parts.append("Consider mentioning: " + ", ".join(missed) + ".")
    if length_factor < 0.5:
        parts.append("Try to elaborate more with an example.")
    return " ".join(parts)


def combine(auto_score: float, self_rating: int | None) -> float:
    if self_rating is None:
        return auto_score
    return round(0.7 * auto_score + 0.3 * self_rating * 20, 1)
