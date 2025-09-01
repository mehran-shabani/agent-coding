"""
LLM communication module for Local Coding Agent.
"""

import json
import time
from typing import Any, Dict, List, Optional

import openai
from rich.console import Console

from .config import get_config
from .prompts import SYSTEM_PROMPT

console = Console()


class LLMClient:
    """Client for communicating with LLM services."""
    
    def __init__(self):
        self.config = get_config()
        self.client = openai.OpenAI(
            api_key=self.config.llm_api_key,
            base_url=self.config.llm_base_url,
        )
        self.max_retries = 3
        self.retry_delay = 1
    
    def _create_messages(
        self, 
        prompt: str, 
        system_prompt: str = SYSTEM_PROMPT,
        context: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Create messages for LLM request."""
        messages = [{"role": "system", "content": system_prompt}]
        
        if context:
            messages.append({"role": "user", "content": f"Context:\n{context}\n\nRequest:\n{prompt}"})
        else:
            messages.append({"role": "user", "content": prompt})
        
        return messages
    
    def _make_request(self, messages: List[Dict[str, str]]) -> str:
        """Make request to LLM with retry logic."""
        for attempt in range(self.max_retries):
            try:
                # Try responses.create first (for some API endpoints)
                try:
                    response = self.client.responses.create(
                        model=self.config.llm_model,
                        messages=messages,
                        max_tokens=4000,
                        temperature=0.1,
                    )
                    return response.choices[0].message.content
                except (AttributeError, Exception):
                    # Fallback to chat.completions.create
                    response = self.client.chat.completions.create(
                        model=self.config.llm_model,
                        messages=messages,
                        max_tokens=4000,
                        temperature=0.1,
                    )
                    return response.choices[0].message.content
                    
            except Exception as e:
                if attempt < self.max_retries - 1:
                    console.print(f"[yellow]Attempt {attempt + 1} failed: {e}. Retrying...[/yellow]")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise Exception(f"LLM request failed after {self.max_retries} attempts: {e}")
        
        raise Exception("LLM request failed")
    
    def ask(
        self, 
        prompt: str, 
        system_prompt: str = SYSTEM_PROMPT,
        context: Optional[str] = None
    ) -> str:
        """Ask a question to the LLM."""
        messages = self._create_messages(prompt, system_prompt, context)
        return self._make_request(messages)
    
    def generate_file_content(self, description: str, context: Optional[str] = None) -> str:
        """Generate file content from description."""
        from .prompts import FILE_GENERATION_PROMPT
        
        prompt = f"Generate file content for: {description}"
        return self.ask(prompt, FILE_GENERATION_PROMPT, context)
    
    def edit_file(self, file_content: str, instruction: str) -> str:
        """Generate unified diff for file editing."""
        from .prompts import FILE_EDIT_PROMPT
        
        prompt = f"File content:\n{file_content}\n\nInstruction: {instruction}\n\nGenerate unified diff:"
        return self.ask(prompt, FILE_EDIT_PROMPT)
    
    def generate_patch(self, description: str, context: Optional[str] = None) -> str:
        """Generate unified diff patch from description."""
        from .prompts import PATCH_GENERATION_PROMPT
        
        prompt = f"Generate patch for: {description}"
        return self.ask(prompt, PATCH_GENERATION_PROMPT, context)
    
    def analyze_project(self, project_info: str) -> str:
        """Analyze project and generate code map."""
        from .prompts import ANALYSIS_PROMPT
        
        prompt = f"Analyze this project:\n{project_info}"
        return self.ask(prompt, ANALYSIS_PROMPT)
    
    def create_plan(self, goal: str, context: Optional[str] = None) -> str:
        """Create a plan for achieving a goal."""
        from .prompts import PLANNING_PROMPT
        
        prompt = f"Create a plan for: {goal}"
        return self.ask(prompt, PLANNING_PROMPT, context)
    
    def manage_todo(self, action: str, content: str) -> str:
        """Manage TODO items."""
        from .prompts import TODO_PROMPT
        
        prompt = f"TODO {action}: {content}"
        return self.ask(prompt, TODO_PROMPT)


# Global LLM client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get the global LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client