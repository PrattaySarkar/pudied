from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .models import Article, ArticleRecord

LOG = logging.getLogger(__name__)
RESERVED = {"_metadata.json"}


def display_name(value: str) -> str:
    return " ".join(part.capitalize() for part in value.replace("_", "-").split("-"))


@dataclass
class ScanResult:
    records: dict[str, ArticleRecord] = field(default_factory=dict)
    errors: list[dict[str, str]] = field(default_factory=list)
    duplicates: list[dict[str, str]] = field(default_factory=list)
    scanned_at: float = 0.0

    @property
    def articles(self) -> list[ArticleRecord]:
        return sorted(self.records.values(), key=lambda r: r.article.title.casefold())


class DataScanner:
    def __init__(self, data_dir: str | Path, cache_seconds: float = 2.0) -> None:
        self.data_dir = Path(data_dir).resolve()
        self.cache_seconds = max(0.0, cache_seconds)
        self._result: ScanResult | None = None
        self._lock = threading.Lock()
        self.scan_count = 0

    def get(self, force: bool = False) -> ScanResult:
        now = time.monotonic()
        if not force and self._result and now - self._result.scanned_at < self.cache_seconds:
            return self._result
        with self._lock:
            now = time.monotonic()
            if not force and self._result and now - self._result.scanned_at < self.cache_seconds:
                return self._result
            self._result = self._scan()
            return self._result

    def _scan(self) -> ScanResult:
        result = ScanResult(scanned_at=time.monotonic())
        self.scan_count += 1
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            result.errors.append({"path": "data", "message": f"Cannot access data directory: {exc}"})
            return result
        try:
            files = sorted(self.data_dir.rglob("*"))
        except OSError as exc:
            result.errors.append({"path": "data", "message": f"Cannot scan data directory: {exc}"})
            return result
        for path in files:
            if not path.is_file() or path.is_symlink() or path.name.startswith("."):
                continue
            if path.suffix.casefold() != ".json" or path.name in RESERVED:
                continue
            self._read_file(path, result)
        return result

    def _read_file(self, path: Path, result: ScanResult) -> None:
        try:
            relative = path.resolve().relative_to(self.data_dir)
        except (ValueError, OSError):
            result.errors.append({"path": path.name, "message": "Unsafe path outside data directory"})
            return
        source = relative.as_posix()
        try:
            raw: Any = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            result.errors.append({"path": source, "message": f"Invalid JSON: {exc}"})
            return
        if not isinstance(raw, dict):
            result.errors.append({"path": source, "message": "Article JSON must be an object"})
            return
        try:
            article = Article.model_validate(raw)
        except ValidationError as exc:
            result.errors.append({"path": source, "message": "; ".join(e["msg"] for e in exc.errors())})
            return
        categories = tuple(relative.parent.parts)
        record = ArticleRecord(article=article, source_path=source, category_path=categories)
        if article.id in result.records:
            result.duplicates.append({"id": article.id, "paths": f"{result.records[article.id].source_path}, {source}"})
            result.errors.append({"path": source, "message": f"Duplicate article id: {article.id}"})
            return
        result.records[article.id] = record

    def tree(self, force: bool = False) -> dict[str, Any]:
        result = self.get(force)
        root: dict[str, Any] = {"name": "PUDIED", "path": "", "categories": {}, "articles": [], "article_count": 0}
        for record in result.articles:
            node = root
            node["article_count"] += 1
            for index, part in enumerate(record.category_path):
                node = node["categories"].setdefault(part, {"name": display_name(part), "path": "/".join(record.category_path[:index + 1]), "categories": {}, "articles": [], "article_count": 0})
                node["article_count"] += 1
            node["articles"].append({"id": record.article.id, "title": record.article.title})
        return root

    def category(self, parts: tuple[str, ...], force: bool = False) -> dict[str, Any] | None:
        node = self.tree(force)
        for part in parts:
            if part not in node["categories"]:
                return None
            node = node["categories"][part]
        return node

    def validate_references(self, result: ScanResult | None = None) -> list[dict[str, str]]:
        result = result or self.get()
        errors = list(result.errors)
        for record in result.articles:
            for related in record.article.related_articles:
                if related not in result.records:
                    errors.append({"path": record.source_path, "message": f"Broken related article reference: {related}"})
        return errors

