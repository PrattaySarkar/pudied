from __future__ import annotations

import os
import random
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .renderer import create_templates
from .scanner import DataScanner
from .search import search

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("PUDIED_DATA_DIR", BASE_DIR / "data"))
scanner = DataScanner(DATA_DIR, float(os.getenv("PUDIED_CACHE_SECONDS", "2")))
templates = create_templates()
app = FastAPI(title="PUDIED", description="Prattay's Urban Dictionary of Interesting Engineering Decisions")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")


def context(request: Request, **values: object) -> dict[str, object]:
    path = request.url.path.strip("/").split("/")
    current_article_id = path[1] if len(path) == 2 and path[0] == "article" else None
    current_category = tuple(path[1:]) if path and path[0] == "category" else ()
    if current_article_id:
        record = scanner.get().records.get(current_article_id)
        current_category = record.category_path if record else ()
    return {"request": request, "tree": scanner.tree(), "current_category": current_category, "current_article_id": current_article_id, **values}


def render(template_name: str, request: Request, status_code: int = 200, **values: object):
    return templates.TemplateResponse(request=request, name=template_name, context=context(request, **values), status_code=status_code)


@app.on_event("startup")
def startup() -> None:
    scanner.get(force=True)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    result = scanner.get()
    recent = sorted(result.articles, key=lambda r: (r.article.updated_at or r.article.created_at or "", r.article.title), reverse=True)[:6]
    return render("home.html", request, recent=recent, errors=result.errors)


@app.get("/article/{article_id}", response_class=HTMLResponse)
def article_page(request: Request, article_id: str):
    result = scanner.get()
    record = result.records.get(article_id)
    if record is None:
        result = scanner.get(force=True)
        record = result.records.get(article_id)
    if record is None:
        return render("404.html", request, status_code=404, message="That entry is not in the current index.")
    related = [result.records[r] for r in record.article.related_articles if r in result.records]
    return render("article.html", request, record=record, related=related)


@app.get("/category/{category_path:path}", response_class=HTMLResponse)
def category_page(request: Request, category_path: str):
    parts = tuple(p for p in category_path.split("/") if p)
    if any(p in {".", ".."} or "\\" in p for p in parts):
        raise HTTPException(status_code=400, detail="Invalid category path")
    node = scanner.category(parts)
    if node is None:
        return render("404.html", request, status_code=404, message="That category is not in the current tree.")
    return render("category.html", request, node=node, parts=parts)


@app.get("/tree", response_class=HTMLResponse)
def tree_page(request: Request):
    return render("tree.html", request)


@app.get("/search", response_class=HTMLResponse)
def search_page(request: Request, q: str = Query(default="")):
    matches = search(scanner.get().articles, q)
    return render("search.html", request, q=q, matches=matches)


@app.get("/index", response_class=HTMLResponse)
def index_page(request: Request):
    return render("index.html", request, records=scanner.get().articles)


@app.get("/surprise")
def surprise():
    records = scanner.get().articles
    if not records:
        return RedirectResponse(url="/index", status_code=303)
    return RedirectResponse(url=f"/article/{random.choice(records).article.id}", status_code=303)


@app.get("/api/tree")
def tree_api():
    return scanner.tree()


@app.get("/api/articles")
def articles_api():
    result = scanner.get()
    return {"articles": [record.public_dict() for record in result.articles], "errors": result.errors, "count": len(result.records)}


@app.get("/api/articles/{article_id}")
def article_api(article_id: str):
    record = scanner.get().records.get(article_id) or scanner.get(force=True).records.get(article_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return record.public_dict()


@app.post("/api/refresh")
@app.get("/api/refresh")
def refresh_api():
    result = scanner.get(force=True)
    return {"status": "refreshed", "count": len(result.records), "errors": scanner.validate_references(result)}


@app.get("/health")
def health():
    result = scanner.get()
    return {"status": "ok", "articles": len(result.records), "scan_age_seconds": round(max(0, __import__('time').monotonic() - result.scanned_at), 3)}

