"""Configuration management for the Local Coding Agent."""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class AgentConfig(BaseSettings):
    """Main configuration for the LCA agent."""
    
    # LLM Configuration
    llm_api_key: str = Field(..., description="API key for LLM service")
    llm_base_url: str = Field("https://api.gapgpt.app/v1", description="Base URL for LLM API")
    llm_model: str = Field("gpt-5o", description="LLM model name")
    
    # Agent Configuration
    agent_workdir: Path = Field(Path("."), description="Working directory for agent operations")
    agent_log_dir: Path = Field(Path(".agent/logs"), description="Directory for log files")
    agent_state: Path = Field(Path(".agent/state.json"), description="Path to state file")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @validator("agent_workdir", "agent_log_dir", "agent_state", pre=True)
    def expand_path(cls, v):
        """Expand paths and ensure they are absolute."""
        if isinstance(v, str):
            v = Path(v)
        return v.expanduser().resolve()
    
    @validator("llm_api_key")
    def validate_api_key(cls, v):
        """Ensure API key is provided."""
        if not v:
            raise ValueError("LLM_API_KEY must be set in environment or .env file")
        return v
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        self.agent_log_dir.mkdir(parents=True, exist_ok=True)
        self.agent_state.parent.mkdir(parents=True, exist_ok=True)
        reports_dir = self.agent_state.parent / "reports"
        reports_dir.mkdir(exist_ok=True)


def load_config() -> AgentConfig:
    """Load and validate configuration."""
    try:
        config = AgentConfig()
        config.ensure_directories()
        return config
    except Exception as e:
        print(f"Error loading configuration: {e}")
        raise SystemExit(1)