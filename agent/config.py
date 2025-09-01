from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError


class Settings(BaseModel):
    llm_api_key: str = Field(alias="LLM_API_KEY")
    llm_base_url: str = Field(default="https://api.gapgpt.app/v1", alias="LLM_BASE_URL")
    llm_model: str = Field(default="gpt-5o", alias="LLM_MODEL")
    agent_workdir: str = Field(default=".", alias="AGENT_WORKDIR")
    agent_log_dir: str = Field(default=".agent/logs", alias="AGENT_LOG_DIR")
    agent_state: str = Field(default=".agent/state.json", alias="AGENT_STATE")


def load_settings(env_path: Optional[os.PathLike] = None) -> Settings:
    load_dotenv(dotenv_path=env_path, override=False)
    try:
        settings = Settings.model_validate({
            "LLM_API_KEY": os.getenv("LLM_API_KEY", ""),
            "LLM_BASE_URL": os.getenv("LLM_BASE_URL", "https://api.gapgpt.app/v1"),
            "LLM_MODEL": os.getenv("LLM_MODEL", "gpt-5o"),
            "AGENT_WORKDIR": os.getenv("AGENT_WORKDIR", "."),
            "AGENT_LOG_DIR": os.getenv("AGENT_LOG_DIR", ".agent/logs"),
            "AGENT_STATE": os.getenv("AGENT_STATE", ".agent/state.json"),
        })
    except ValidationError as exc:
        raise SystemExit(f"LLM_API_KEY is required. Define it in .env or environment. Details: {exc}")

    # ensure directories exist
    Path(settings.agent_log_dir).mkdir(parents=True, exist_ok=True)
    Path(os.path.dirname(settings.agent_state)).mkdir(parents=True, exist_ok=True)
    return settings
