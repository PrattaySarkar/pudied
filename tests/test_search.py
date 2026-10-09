from app.search import search


def test_searches_all_content_fields(scanner, article_json):
    article_json(scanner.data_dir, "a.json", "alpha", aliases=["Blue Widget"], tags=["rare-tag"], examples=["use the banana"])
    records = scanner.get(force=True).articles
    assert search(records, "blue")[0][0].article.id == "alpha"
    assert search(records, "rare-tag")[0][0].article.id == "alpha"
    assert search(records, "banana")[0][0].article.id == "alpha"
