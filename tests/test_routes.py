from fastapi.testclient import TestClient

from app import main


def test_routes_and_live_api(tmp_path, article_json, monkeypatch):
    article_json(tmp_path / "data", "general/hello.json", "hello", related_articles=[])
    monkeypatch.setattr(main, "scanner", __import__("app.scanner", fromlist=["DataScanner"]).DataScanner(tmp_path / "data", cache_seconds=0))
    client = TestClient(main.app)
    assert client.get("/health").status_code == 200
    assert client.get("/").status_code == 200
    assert client.get("/tree").status_code == 200
    assert client.get("/article/hello").status_code == 200
    assert client.get("/api/articles/hello").status_code == 200
    assert client.get("/article/nope").status_code == 404
    assert client.get("/api/refresh").json()["status"] == "refreshed"


def test_path_traversal_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "scanner", __import__("app.scanner", fromlist=["DataScanner"]).DataScanner(tmp_path / "data", cache_seconds=0))
    client = TestClient(main.app)
    assert client.get("/category/../secret").status_code in {400, 404}
