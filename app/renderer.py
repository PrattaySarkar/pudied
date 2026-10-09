from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates

from .scanner import display_name


def create_templates() -> Jinja2Templates:
    templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
    templates.env.filters["display_name"] = display_name
    return templates

