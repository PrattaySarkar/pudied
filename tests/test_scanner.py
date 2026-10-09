import json
import time


def test_discovers_direct_and_nested_articles(scanner, article_json):
    article_json(scanner.data_dir, "one.json", "one")
    article_json(scanner.data_dir, "mecheng/fixtures/two.json", "two")
    result = scanner.get(force=True)
    assert set(result.records) == {"one", "two"}
    assert result.records["two"].category_path == ("mecheng", "fixtures")


def test_live_create_edit_delete_and_new_category(scanner, article_json):
    article_json(scanner.data_dir, "initial.json", "initial")
    scanner.get(force=True)
    article_json(scanner.data_dir, "new/nested/entry.json", "new-entry", definition="before")
    assert "new-entry" in scanner.get().records
    time.sleep(0.03)
    path = scanner.data_dir / "new/nested/entry.json"
    payload = json.loads(path.read_text())
    payload["definition"] = "after"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert scanner.get().records["new-entry"].article.definition == "after"
    path.unlink()
    assert "new-entry" not in scanner.get(force=True).records


def test_malformed_and_duplicate_are_reported(scanner, article_json):
    article_json(scanner.data_dir, "a.json", "same")
    article_json(scanner.data_dir, "b.json", "same")
    (scanner.data_dir / "bad.json").write_text("{not json", encoding="utf-8")
    result = scanner.get(force=True)
    assert len(result.records) == 1
    assert any("Duplicate" in item["message"] for item in result.errors)
    assert any("Invalid JSON" in item["message"] for item in result.errors)


def test_tree_and_broken_related_reference(scanner, article_json):
    article_json(scanner.data_dir, "a/b.json", "known", related_articles=["missing"])
    tree = scanner.tree(force=True)
    assert tree["categories"]["a"]["article_count"] == 1
    assert any("Broken related" in item["message"] for item in scanner.validate_references())


def test_cache_prevents_repeated_scans(scanner, article_json):
    article_json(scanner.data_dir, "a.json")
    scanner.get(force=True)
    count = scanner.scan_count
    scanner.get()
    scanner.get()
    assert scanner.scan_count == count
