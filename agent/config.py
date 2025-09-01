"""
Configuration management for Local Coding Agent.
"""

import os
from pathlib import Path
from typing import Optional

import pydantic
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config(pydantic.BaseModel):
    """Configuration model for the Local Coding Agent."""
    
    # LLM Configuration
    llm_api_key: str = pydantic.Field(..., description="LLM API Key")
    llm_base_url: str = pydantic.Field(
        default="https://api.gapgpt.app/v1",
        description="LLM Base URL"
    )
    llm_model: str = pydantic.Field(
        default="gpt-5o",
        description="LLM Model name"
    )
    
    # Agent Configuration
    agent_workdir: Path = pydantic.Field(
        default=Path("."),
        description="Agent working directory"
    )
    agent_log_dir: Path = pydantic.Field(
        default=Path(".agent/logs"),
        description="Agent log directory"
    )
    agent_state: Path = pydantic.Field(
        default=Path(".agent/state.json"),
        description="Agent state file path"
    )
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        # Check for required API key
        api_key = os.getenv("LLM_API_KEY")
        if not api_key:
            raise ValueError(
                "LLM_API_KEY environment variable is required. "
                "Please set it in your .env file or environment."
            )
        
        return cls(
            llm_api_key=api_key,
            llm_base_url=os.getenv("LLM_BASE_URL", "https://api.gapgpt.app/v1"),
            llm_model=os.getenv("LLM_MODEL", "gpt-5o"),
            agent_workdir=Path(os.getenv("AGENT_WORKDIR", ".")),
            agent_log_dir=Path(os.getenv("AGENT_LOG_DIR", ".agent/logs")),
            agent_state=Path(os.getenv("AGENT_STATE", ".agent/state.json")),
        )
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        self.agent_log_dir.mkdir(parents=True, exist_ok=True)
        self.agent_state.parent.mkdir(parents=True, exist_ok=True)
    
    def get_log_file(self, name: str) -> Path:
        """Get log file path for a specific operation."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.agent_log_dir / f"{name}-{timestamp}.log"
    
    def get_report_file(self, name: str) -> Path:
        """Get report file path for a specific operation."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = Path(".agent/reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        return report_dir / f"{name}-{timestamp}.md"
    
    def get_contradiction_report(self) -> Path:
        """Get contradiction report file path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = Path(".agent/reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        return report_dir / f"contradictions-{timestamp}.md"


# Global configuration instance
config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global config
    if config is None:
        config = Config.from_env()
        config.ensure_directories()
    return config