"""
Root ASGI Entrypoint for ResilioAI Engine.
Memungkinkan deployment server berjalan baik dengan 'uvicorn app.main:app' maupun 'uvicorn main:app'.
"""

from app.main import app

__all__ = ["app"]
