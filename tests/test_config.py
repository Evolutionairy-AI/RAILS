import pytest

from rails_ref.config import load_key


def test_load_key_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-ENVVALUE")
    assert load_key("openai") == "sk-test-ENVVALUE"


def test_load_key_from_file(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    (tmp_path / "OpenAI_RI.key.txt").write_text("sk-proj-FILEVALUE\n")
    assert load_key("openai", keydir=tmp_path).startswith("sk-proj-")


def test_load_key_missing_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    (tmp_path / "Claude_Key.txt").write_text("no key here")
    with pytest.raises(ValueError):
        load_key("anthropic", keydir=tmp_path)


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        load_key("gemini")
