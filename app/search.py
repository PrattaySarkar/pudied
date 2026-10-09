from __future__ import annotations

import re

from .models import ArticleRecord


def search(records: list[ArticleRecord], query: str) -> list[tuple[ArticleRecord, int]]:
    terms = [t for t in re.findall(r"[\w-]+", query.casefold()) if t]
    if not terms:
        return []
    ranked: list[tuple[ArticleRecord, int]] = []
    for record in records:
        article = record.article
        fields = [article.title, *(article.aliases), *(article.tags), article.summary or "", article.definition, *(article.examples)]
        score = sum((5 if term in article.title.casefold() else 0) + sum(1 for field in fields if term in field.casefold()) for term in terms)
        if score:
            ranked.append((record, score))
    return sorted(ranked, key=lambda item: (-item[1], item[0].article.title.casefold()))

