from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class Article(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    category: str | None = None
    summary: str | None = None
    part_of_speech: str | None = None
    tags: list[str] = Field(default_factory=list)
    origin: str | None = None
    examples: list[str] = Field(default_factory=list)
    related_articles: list[str] = Field(default_factory=list)
    related_terms: list[str] = Field(default_factory=list)
    root_cause: str | None = None
    created_at: date | None = None
    updated_at: date | None = None

    def search_text(self) -> str:
        values: list[str] = [self.title, self.definition, self.summary or "", *self.aliases, *self.tags, *self.examples]
        return " ".join(values).lower()


class ArticleRecord(BaseModel):
    article: Article
    source_path: str
    category_path: tuple[str, ...]

    def public_dict(self) -> dict[str, Any]:
        data = self.article.model_dump(mode="json")
        data["category_path"] = list(self.category_path)
        data["source_path"] = self.source_path
        return data

