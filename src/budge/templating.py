"""The shared Jinja environment every view renders through."""

from pathlib import Path

from fastapi.templating import Jinja2Templates

# Inside the package, so it resolves the same from source or site-packages.
TEMPLATE_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"

templates = Jinja2Templates(directory=TEMPLATE_DIR)
