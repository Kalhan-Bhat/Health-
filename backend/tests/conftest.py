"""Shared pytest setup.

A dummy API key is set *before* the app is imported so tests never need a real
Groq key and never call the real Groq API (live tests are marked `@pytest.mark.live`).
"""

import os

os.environ.setdefault("GROQ_API_KEY", "test-key-not-real")
os.environ.setdefault("APP_ENV", "development")
