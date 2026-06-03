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


def test_load_gemini_key_from_file(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    (tmp_path / "Gemini_RAILS_Key.txt").write_text("AIzaSyExampleExampleExampleExample1234\n")
    assert load_key("gemini", keydir=tmp_path).startswith("AIza")


def test_load_mistral_key_from_file(tmp_path, monkeypatch):
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    (tmp_path / "Mistral_RI_Key.txt").write_text("AbCd1234EfGh5678IjKl9012MnOp3456\n")
    assert len(load_key("mistral", keydir=tmp_path)) >= 24


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        load_key("cohere")
