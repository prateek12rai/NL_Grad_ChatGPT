"""Groq mock flag must respect repo .env over stale OS environment."""

from pathlib import Path


def test_dotenv_groq_mock_false_when_file_says_false(monkeypatch):
    monkeypatch.setenv("GROQ_MOCK", "true")
    from shared.config import Settings

    s = Settings()
    if Path(".env").is_file():
        assert s.groq_mock is False
        assert s.groq_live is True
