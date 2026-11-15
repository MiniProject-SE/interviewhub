"""Small text utilities shared by the recommender and the answer scorer."""
import re

STOPWORDS = frozenset(
    """a an the and or but if then else of to in on for with at by from as is are was were be
    been being it its this that these those i you he she we they me my your our their what which
    who whom how why when where can could should would will shall may might do does did done have
    has had not no yes so than too very just about into over under again also any each few more
    most other some such only own same both all there here up down out off between through during
    before after above below explain describe tell give""".split()
)

_TOKEN_RE = re.compile(r"[a-z0-9+#]+")


def tokenize(text: str) -> list[str]:
    """Lower-case word tokens with stop-words removed. Keeps c++ / c# style tokens."""
    if not text:
        return []
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in STOPWORDS and len(t) > 1]


def split_tags(tags: str | None) -> list[str]:
    if not tags:
        return []
    return [t.strip().lower() for t in tags.split(",") if t.strip()]
