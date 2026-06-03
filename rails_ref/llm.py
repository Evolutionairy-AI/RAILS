"""Cached LLM-judge wrapper over the Anthropic and OpenAI SDKs.

Every response is cached on disk keyed by (provider, model, temperature, prompt)
so the headline experiment is reproducible and free to replay without keys. The
backend is injectable (`_backend`) so tests never hit the network.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path


class LLMJudge:
    def __init__(self, provider: str, model: str, cache_dir: Path | str,
                 temperature: float = 0.0, max_tokens: int = 300, _backend=None):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._backend = _backend  # callable(prompt=...) -> raw str; for tests

    def _cache_key(self, prompt: str) -> str:
        h = hashlib.sha256()
        h.update(f"{self.provider}|{self.model}|{self.temperature}|{prompt}".encode("utf-8"))
        return h.hexdigest()

    def judge(self, prompt: str) -> dict:
        path = self.cache_dir / f"{self._cache_key(prompt)}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        raw = self._call_backend(prompt)
        parsed = self._parse(raw)
        path.write_text(json.dumps(parsed), encoding="utf-8")
        return parsed

    def _call_backend(self, prompt: str) -> str:
        if self._backend is not None:
            return self._backend(prompt=prompt)
        return self._real_backend(prompt)

    def _real_backend(self, prompt: str) -> str:
        from rails_ref.config import load_key
        msgs = [{"role": "user", "content": prompt}]
        if self.provider == "anthropic":
            from anthropic import Anthropic
            client = Anthropic(api_key=load_key("anthropic"))
            base = {"model": self.model, "max_tokens": self.max_tokens, "messages": msgs}
            try:
                r = client.messages.create(temperature=self.temperature, **base)
            except Exception as e:  # newer models (e.g. Opus 4.8) deprecate temperature
                if "temperature" in str(e).lower():
                    r = client.messages.create(**base)
                else:
                    raise
            return r.content[0].text
        if self.provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=load_key("openai"))
            if self.model.startswith(("gpt-5", "o1", "o3", "o4")):
                # reasoning-capable models: budget must cover hidden reasoning, only
                # the default temperature is accepted, and 'minimal' effort is rejected
                # by some — fall back to default effort if 'low' is unsupported.
                base = {"model": self.model, "messages": msgs,
                        "max_completion_tokens": max(self.max_tokens, 2048)}
                try:
                    r = client.chat.completions.create(reasoning_effort="low", **base)
                except Exception as e:
                    if "reasoning_effort" in str(e).lower():
                        r = client.chat.completions.create(**base)
                    else:
                        raise
            else:
                r = client.chat.completions.create(
                    model=self.model, max_tokens=self.max_tokens,
                    temperature=self.temperature, messages=msgs)
            return r.choices[0].message.content
        if self.provider == "mistral":
            # Mistral exposes an OpenAI-compatible endpoint.
            from openai import OpenAI
            client = OpenAI(api_key=load_key("mistral"), base_url="https://api.mistral.ai/v1")
            r = client.chat.completions.create(
                model=self.model, max_tokens=self.max_tokens, temperature=self.temperature,
                messages=msgs)
            return r.choices[0].message.content
        if self.provider == "gemini":
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=load_key("gemini"))
            # Gemini 2.5/3 "think" by default; give output budget room so the visible
            # verdict survives, and keep thinking minimal on models that allow it.
            cfg = types.GenerateContentConfig(
                temperature=self.temperature, max_output_tokens=max(self.max_tokens, 2048))
            r = client.models.generate_content(model=self.model, contents=prompt, config=cfg)
            return r.text or ""
        raise ValueError(f"unknown provider: {self.provider}")

    @staticmethod
    def _parse(raw: str) -> dict:
        text = (raw or "").strip()
        up = text.upper()
        m = re.search(r"VERDICT\s*[:\-]\s*(PASS|FAIL)", up)
        if m:
            verdict = m.group(1)
        elif "PASS" in up and "FAIL" not in up:
            verdict = "PASS"
        elif "FAIL" in up:
            verdict = "FAIL"
        else:
            verdict = "ABSTAIN"
        bm = re.search(r"BASIS\s*[:\-]\s*(SELF|SIGN|WIT|REC|ATT|PROOF)", up)
        basis = bm.group(1) if bm else None
        return {"verdict": verdict, "basis": basis, "raw": text}
