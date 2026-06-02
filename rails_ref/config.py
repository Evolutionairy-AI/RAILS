"""Configuration and secure API-key loading.

Importing this module injects the OS (Windows) certificate store into Python's
SSL via truststore — MANDATORY on this machine, where a TLS-inspection CA
otherwise fails certificate verification for api.openai.com / api.anthropic.com.

Keys are resolved from environment variables first, then from the key files in
the API_KEYS directory (which lives OUTSIDE this repo and is never committed).
Key values are never logged.
"""
from __future__ import annotations
import os
import re
from pathlib import Path

import truststore
truststore.inject_into_ssl()

DEFAULT_KEYDIR = Path(r"D:\EvolutionAIry\RAILS\API_KEYS")
KEY_FILES = {"anthropic": "Claude_Key.txt", "openai": "OpenAI_RI.key.txt"}
ENV_VARS = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}


def load_key(provider: str, keydir: Path | str | None = None) -> str:
    """Return the API key for `provider` ('anthropic' or 'openai').

    Env var wins; otherwise read the provider's key file and extract an
    `sk-...` token. Raises ValueError if no key can be found.
    """
    provider = provider.lower()
    if provider not in ENV_VARS:
        raise ValueError(f"unknown provider: {provider}")

    env = os.environ.get(ENV_VARS[provider])
    if env:
        return env.strip()

    base = Path(keydir) if keydir else DEFAULT_KEYDIR
    path = base / KEY_FILES[provider]
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"sk-[A-Za-z0-9_\-]+", text)
    if not m:
        raise ValueError(f"no API key found in {path.name}")
    return m.group(0)
