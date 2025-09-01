from __future__ import annotations

from typing import List, Dict

from openai import OpenAI

from .config import Config


def _build_client(cfg: Config) -> OpenAI:
    return OpenAI(base_url=cfg.llm_base_url, api_key=cfg.llm_api_key)


def ask(cfg: Config, messages: List[Dict[str, str]]) -> str:
    client = _build_client(cfg)
    # Try Responses API first
    try:
        resp = client.responses.create(model=cfg.llm_model, input=messages)
        # "output_text" is the unified text helper
        text = getattr(resp, "output_text", None)
        if text:
            return text
        # Fallback for older SDK shapes
        if hasattr(resp, "choices") and resp.choices:
            return resp.choices[0].message.content  # type: ignore[attr-defined]
    except Exception:
        pass
    # Fallback to chat.completions
    chat = client.chat.completions.create(model=cfg.llm_model, messages=messages)
    return chat.choices[0].message.content or ""
