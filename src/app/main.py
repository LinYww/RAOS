"""ASGI entrypoint exposed to process managers and local runners."""

from app.api.app import create_app


app = create_app()
