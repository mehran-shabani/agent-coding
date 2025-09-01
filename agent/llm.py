from __future__ import annotations

from typing import List, Dict, Any

from openai import OpenAI


class LLMClient:
    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def ask(self, messages: List[Dict[str, str]]) -> str:
        try:
            resp = self.client.responses.create(model=self.model, input=messages)
            # OpenAI responses return output in various formats; pick text aggregate if present
            if hasattr(resp, "output") and getattr(resp, "output", None):
                return str(resp.output)
            if hasattr(resp, "content") and resp.content:
                parts = []
                for item in resp.content:
                    if getattr(item, "type", None) == "output_text":
                        parts.append(getattr(item, "text", ""))
                if parts:
                    return "".join(parts)
            # fallback stringify
            return str(resp)
        except Exception:
            # fallback to chat.completions
            chat = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
            )
            return chat.choices[0].message.get("content", "")
