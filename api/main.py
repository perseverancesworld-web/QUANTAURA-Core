"""DEPRECATED.

The real FastAPI application lives at quantaura.api.main.
This file remains only to avoid breaking old references.

Use:
    quantaura-serve --reload
    # or
    uvicorn quantaura.api.main:app --reload
"""

from quantaura.api.main import app  # noqa: F401

if __name__ == "__main__":
    from quantaura.api.main import cli_serve

    cli_serve()
