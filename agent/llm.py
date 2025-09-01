"""LLM integration module using OpenAI client."""

import json
from typing import Dict, List, Optional, Any
from openai import OpenAI
from rich.console import Console

from .config import AgentConfig


console = Console()


class LLMClient:
    """Client for interacting with LLM API."""
    
    def __init__(self, config: AgentConfig):
        """Initialize LLM client with configuration."""
        self.config = config
        self.client = OpenAI(
            api_key=config.llm_api_key,
            base_url=config.llm_base_url
        )
        self.model = config.llm_model
    
    def _call_llm(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """Internal method to call LLM with fallback."""
        try:
            # Try responses.create first (if available)
            if hasattr(self.client, 'responses'):
                response = self.client.responses.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature
                )
                return response.choices[0].message.content
        except Exception:
            pass
        
        # Fallback to chat.completions.create
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            console.print(f"[red]Error calling LLM: {e}[/red]")
            raise
    
    def ask(self, question: str, system_prompt: Optional[str] = None) -> str:
        """Ask a question to the LLM."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": question})
        
        return self._call_llm(messages)
    
    def generate_code(self, description: str, file_type: Optional[str] = None) -> str:
        """Generate code based on description."""
        system_prompt = (
            "You are a local coding agent. Generate clean, minimal, and functional code. "
            "Only return the code without any explanation or markdown formatting."
        )
        
        prompt = description
        if file_type:
            prompt = f"Generate a {file_type} file: {description}"
        
        return self._call_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ], temperature=0.3)
    
    def generate_patch(self, file_content: str, instruction: str) -> str:
        """Generate a unified diff patch for file modification."""
        system_prompt = (
            "You are a local coding agent. Generate a unified diff patch to modify the given file. "
            "Only output the patch in unified diff format, nothing else. "
            "The patch should be minimal and only change what's necessary."
        )
        
        user_prompt = f"""File content:
```
{file_content}
```

Instruction: {instruction}

Generate a unified diff patch for this change."""
        
        return self._call_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ], temperature=0.3)
    
    def generate_multi_file_patch(self, project_context: str, description: str) -> str:
        """Generate patches for multiple files."""
        system_prompt = (
            "You are a local coding agent. Generate unified diff patches for multiple files. "
            "Output patches with relative paths from project root. "
            "Each file should have its own hunk. Only output the patches, nothing else."
        )
        
        user_prompt = f"""Project context:
{project_context}

Task: {description}

Generate unified diff patches for all necessary changes."""
        
        return self._call_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ], temperature=0.3)
    
    def plan_task(self, goal: str, context: Optional[str] = None) -> List[str]:
        """Generate a plan for achieving a goal."""
        system_prompt = (
            "You are a local coding agent. Break down the goal into clear, actionable steps. "
            "Return a JSON array of strings, each representing one step. Be concise."
        )
        
        prompt = f"Goal: {goal}"
        if context:
            prompt += f"\n\nContext:\n{context}"
        
        response = self._call_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ], temperature=0.5)
        
        try:
            # Try to parse as JSON
            steps = json.loads(response)
            if isinstance(steps, list):
                return steps
        except json.JSONDecodeError:
            # Fallback: split by newlines and clean up
            steps = [s.strip() for s in response.split('\n') if s.strip()]
            # Remove numbering if present
            cleaned_steps = []
            for step in steps:
                # Remove common numbering patterns
                for prefix in ['- ', '* ', '• ']:
                    if step.startswith(prefix):
                        step = step[len(prefix):]
                        break
                # Remove numeric prefixes like "1. ", "2) ", etc.
                import re
                step = re.sub(r'^\d+[\.\)]\s*', '', step)
                if step:
                    cleaned_steps.append(step)
            return cleaned_steps
        
        return []