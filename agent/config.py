"""Configuration management for the Local Coding Agent."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configuration model for the agent."""
    
    llm_api_key: str = Field(..., description="LLM API key")
    llm_base_url: str = Field(default="https://api.gapgpt.app/v1", description="LLM base URL")
    llm_model: str = Field(default="gpt-5o", description="LLM model name")
    agent_workdir: Path = Field(default=Path("."), description="Agent working directory")
    agent_log_dir: Path = Field(default=Path(".agent/logs"), description="Agent log directory")
    agent_state: Path = Field(default=Path(".agent/state.json"), description="Agent state file")
    
    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True


def load_config() -> AgentConfig:
    """Load configuration from environment variables."""
    # Load .env file if it exists
    load_dotenv()
    
    # Check for required API key
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise ValueError(
            "LLM_API_KEY environment variable is required. "
            "Please set it in your .env file or environment."
        )
    
    return AgentConfig(
        llm_api_key=api_key,
        llm_base_url=os.getenv("LLM_BASE_URL", "https://api.gapgpt.app/v1"),
        llm_model=os.getenv("LLM_MODEL", "gpt-5o"),
        agent_workdir=Path(os.getenv("AGENT_WORKDIR", ".")),
        agent_log_dir=Path(os.getenv("AGENT_LOG_DIR", ".agent/logs")),
        agent_state=Path(os.getenv("AGENT_STATE", ".agent/state.json")),
    )


def ensure_directories(config: AgentConfig) -> None:
    """Ensure required directories exist."""
    config.agent_log_dir.mkdir(parents=True, exist_ok=True)
    config.agent_state.parent.mkdir(parents=True, exist_ok=True)
    (config.agent_state.parent / "reports").mkdir(parents=True, exist_ok=True)