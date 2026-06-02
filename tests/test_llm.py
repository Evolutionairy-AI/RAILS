from rails_ref.llm import LLMJudge


def test_cache_hit_returns_without_backend(tmp_path):
    def boom(**k):
        raise AssertionError("backend should not be called on cache hit")
    j = LLMJudge(provider="openai", model="gpt-4.1", cache_dir=tmp_path, _backend=boom)
    key = j._cache_key("PROMPT")
    (tmp_path / f"{key}.json").write_text('{"verdict":"PASS","basis":null,"raw":"PASS"}')
    assert j.judge("PROMPT")["verdict"] == "PASS"


def test_cache_miss_calls_backend_and_persists(tmp_path):
    calls = []
    def backend(prompt):
        calls.append(prompt)
        return "VERDICT: FAIL\nBASIS: ATT"
    j = LLMJudge("openai", "gpt-4.1", cache_dir=tmp_path, _backend=backend)
    out = j.judge("p1")
    assert out["verdict"] == "FAIL" and out["basis"] == "ATT"
    j.judge("p1")  # second call should hit cache
    assert len(calls) == 1


def test_parse_variants():
    assert LLMJudge._parse("VERDICT: PASS")["verdict"] == "PASS"
    assert LLMJudge._parse("After review, I would FAIL this.")["verdict"] == "FAIL"
    assert LLMJudge._parse("VERDICT: PASS\nBASIS: SELF")["basis"] == "SELF"
    assert LLMJudge._parse("unclear")["verdict"] == "ABSTAIN"
