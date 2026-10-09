from pathlib import Path
import pytest

from app.scanner import DataScanner


@pytest.fixture
def article_json():
    def write(root: Path, relative: str, article_id: str = "sample", **extra):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"id": article_id, "title": article_id.title(), "definition": "A useful definition.", **extra}
        path.write_text(__import__("json").dumps(payload), encoding="utf-8")
        return path
    return write


@pytest.fixture
def scanner(tmp_path):
    return DataScanner(tmp_path / "data", cache_seconds=0.02)
