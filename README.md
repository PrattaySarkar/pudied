# PUDIED

**Prattay's Urban Dictionary of Interesting Engineering Decisions** is a live-discovering JSON wiki built with FastAPI, Jinja, and plain CSS/JavaScript.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. Add any valid `.json` file to `data/`, including inside new nested folders. The index is rescanned after the short cache interval, or immediately with `GET /api/refresh`. Set `PUDIED_DATA_DIR` to use another data directory and `PUDIED_CACHE_SECONDS` to change the cache interval.

## Content format

Each article requires string `id`, `title`, and `definition`. Optional fields include `aliases`, `summary`, `category`, `part_of_speech`, `tags`, `origin`, `examples`, `related_articles`, `created_at`, and `updated_at`. Unknown fields are preserved by the model and ignored by the default renderer. The directory path, not the optional `category` field, defines the category hierarchy.

Run the strict checker with:

```bash
python scripts/validate_data.py
```

The live site keeps valid articles available when another file is malformed; the validator exits nonzero so content problems are visible in development or CI.

## Tests

```bash
pytest -q
```

## Render and GitHub

Create a GitHub repository, push this project, and connect it to a Render Web Service. `render.yaml` supplies the build command, production ASGI start command, and `/health` check. A normal Render service packages the JSON files from the deployed commit. Its filesystem is generally ephemeral: files created directly on a running instance can be discovered live, but may disappear after restart or redeploy. A GitHub commit changes the live service only after Render deploys it (unless you add a separate, explicitly configured synchronization workflow).

No article registry is maintained: the filesystem scanner is the source of truth.

## Article submissions

The live site includes `/submit`. It collects an idea in the browser and opens a pre-filled GitHub Issue in this repository for editorial review. This is intentionally free and requires no email provider, database, or Render storage. Since the repository is public, submissions are public GitHub issues; do not submit private information. After review, copy the approved idea into a normal JSON file under `data/`, then deploy that content change.
