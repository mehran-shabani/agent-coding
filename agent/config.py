from __future__ import annotations

import os
import sys
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field


def _now_ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


class Config(BaseModel):
    llm_api_key: Optional[str] = Field(default=None, alias="LLM_API_KEY")
    llm_base_url: str = Field(default="https://api.gapgpt.app/v1", alias="LLM_BASE_URL")
    llm_model: str = Field(default="gpt-5o", alias="LLM_MODEL")

    agent_workdir: str = Field(default=".", alias="AGENT_WORKDIR")
    agent_log_dir: str = Field(default=".agent/logs", alias="AGENT_LOG_DIR")
    agent_state_path: str = Field(default=".agent/state.json", alias="AGENT_STATE")

    class Config:
        populate_by_name = True

    @property
    def workdir_path(self) -> Path:
        return Path(self.agent_workdir).resolve()

    @property
    def log_dir_path(self) -> Path:
        return (self.workdir_path / Path(self.agent_log_dir)).resolve()

    @property
    def reports_dir_path(self) -> Path:
        return (self.workdir_path / ".agent/reports").resolve()

    @property
    def state_file_path(self) -> Path:
        p = Path(self.agent_state_path)
        if not p.is_absolute():
            p = self.workdir_path / p
        return p.resolve()

    def mask_secret(self, value: Optional[str]) -> str:
        if not value:
            return "<missing>"
        if len(value) <= 6:
            return "***"
        return value[:3] + "***" + value[-3:]


def load_config() -> Config:
    # Load environment variables from .env if present
    load_dotenv(override=False)
    cfg = Config()
    return cfg


def ensure_runtime_dirs(cfg: Config) -> None:
    cfg.workdir_path.mkdir(parents=True, exist_ok=True)
    cfg.log_dir_path.mkdir(parents=True, exist_ok=True)
    cfg.reports_dir_path.mkdir(parents=True, exist_ok=True)
    state_parent = cfg.state_file_path.parent
    state_parent.mkdir(parents=True, exist_ok=True)
    if not cfg.state_file_path.exists():
        cfg.state_file_path.write_text(json.dumps({"todos": []}, ensure_ascii=False, indent=2))


def require_api_key(cfg: Config) -> None:
    if not cfg.llm_api_key:
        msg = (
            "LLM_API_KEY is not set. Please set it in your environment or .env file."
        )
        # Also write a contradiction report
        write_contradiction_report(cfg, "Missing LLM_API_KEY while an LLM command was requested.")
        print(msg, file=sys.stderr)
        raise SystemExit(2)


def write_contradiction_report(cfg: Config, details: str) -> Path:
    ensure_runtime_dirs(cfg)
    ts = _now_ts()
    path = cfg.reports_dir_path / f"contradictions-{ts}.md"
    content = (
        f"# Contradiction Detected\n\n"
        f"Time: {datetime.now().isoformat()}\n\n"
        f"Details:\n\n{details}\n"
    )
    path.write_text(content)
    return path


def log_event(cfg: Config, prefix: str, text: str) -> Path:
    ensure_runtime_dirs(cfg)
    ts = _now_ts()
    path = cfg.log_dir_path / f"{prefix}-{ts}.log"
    path.write_text(text)
    return path
