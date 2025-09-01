"""LLM communication layer for the Local Coding Agent."""

import json
import time
from typing import Dict, List, Optional

from openai import OpenAI
from rich.console import Console

from .config import AgentConfig

console = Console()


class LLMClient:
    """Client for communicating with LLM APIs."""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = OpenAI(
            api_key=config.llm_api_key,
            base_url=config.llm_base_url
        )
        self.model = config.llm_model
    
    def chat(self, messages: List[Dict[str, str]], max_retries: int = 3) -> Optional[str]:
        """Send chat messages to LLM and get response."""
        
        for attempt in range(max_retries):
            try:
                console.print(f"[dim]Sending request to LLM (attempt {attempt + 1}/{max_retries})[/dim]")
                
                # Try responses.create first (if available)
                try:
                    response = self.client.responses.create(
                        model=self.model,
                        messages=messages
                    )
                    return response.choices[0].message.content
                except AttributeError:
                    # Fall back to chat.completions.create
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages
                    )
                    return response.choices[0].message.content
                
            except Exception as e:
                console.print(f"[yellow]LLM request failed (attempt {attempt + 1}): {e}[/yellow]")
                if attempt < max_retries - 1:
                    time.sleep(1)  # Brief delay before retry
                else:
                    console.print(f"[red]All LLM requests failed. Last error: {e}[/red]")
                    console.print("[blue]Please check your LLM_API_KEY and LLM_BASE_URL configuration[/blue]")
                    return None
    
    def ask_question(self, question: str, context: Optional[str] = None) -> Optional[str]:
        """Ask a free-form question to the LLM."""
        
        messages = [
            {
                "role": "system",
                "content": "تو یک ایجنت کدنویسی لوکال هستی؛ فقط در workspace تعیین‌شده کار کن؛ تغییرات را به صورت unified diff ارائه بده؛ پاسخ‌ها کوتاه و ایمن باشند."
            }
        ]
        
        if context:
            messages.append({
                "role": "system", 
                "content": f"Context: {context}"
            })
        
        messages.append({
            "role": "user",
            "content": question
        })
        
        return self.chat(messages)
    
    def generate_file_content(self, description: str, file_path: str) -> Optional[str]:
        """Generate file content from description."""
        
        messages = [
            {
                "role": "system",
                "content": "توضیح را به فایل اجرایی تبدیل کن؛ ساختار ساده و مینیمال باشد."
            },
            {
                "role": "user",
                "content": f"Create a file at path '{file_path}' with the following description:\n\n{description}\n\nGenerate only the file content, no explanations."
            }
        ]
        
        return self.chat(messages)
    
    def generate_file_edit(self, file_content: str, file_path: str, instruction: str) -> Optional[str]:
        """Generate edit instructions for a file."""
        
        messages = [
            {
                "role": "system",
                "content": "فقط بخش‌های لازم تغییر کند؛ خروجی unified diff باشد."
            },
            {
                "role": "user",
                "content": f"File path: {file_path}\n\nCurrent content:\n```\n{file_content}\n```\n\nEdit instruction: {instruction}\n\nGenerate a unified diff patch for the changes. Only output the diff, no explanations."
            }
        ]
        
        return self.chat(messages)
    
    def generate_multi_file_patch(self, project_context: str, description: str) -> Optional[str]:
        """Generate a multi-file patch."""
        
        messages = [
            {
                "role": "system",
                "content": "پچ چندفایلی با مسیر نسبی از ریشهٔ پروژه بده؛ هر فایل در hunk جدا باشد."
            },
            {
                "role": "user",
                "content": f"Project context:\n{project_context}\n\nChanges needed:\n{description}\n\nGenerate a unified diff patch for multiple files. Use relative paths from project root."
            }
        ]
        
        return self.chat(messages)
    
    def create_plan(self, goal: str, context: Optional[str] = None) -> Optional[List[str]]:
        """Create a step-by-step plan for achieving a goal."""
        
        messages = [
            {
                "role": "system",
                "content": "یک برنامه‌ریز کدنویسی هستی. گام‌های عملی و قابل اجرا برای دستیابی به هدف ارائه بده."
            }
        ]
        
        if context:
            messages.append({
                "role": "system",
                "content": f"Project context: {context}"
            })
        
        messages.append({
            "role": "user",
            "content": f"Create a step-by-step plan to achieve this goal: {goal}\n\nReturn the plan as a JSON array of strings, where each string is a task step. Only return the JSON, no explanations."
        })
        
        response = self.chat(messages)
        if not response:
            return None
        
        try:
            # Try to parse JSON response
            plan = json.loads(response)
            if isinstance(plan, list) and all(isinstance(step, str) for step in plan):
                return plan
            else:
                console.print("[yellow]LLM returned invalid plan format[/yellow]")
                return None
        except json.JSONDecodeError:
            console.print("[yellow]LLM response was not valid JSON[/yellow]")
            # Try to extract steps from text response
            lines = response.strip().split('\n')
            steps = []
            for line in lines:
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('*') or line.startswith(str(len(steps) + 1))):
                    # Remove bullet points and numbering
                    clean_line = line.lstrip('-*0123456789. ')
                    if clean_line:
                        steps.append(clean_line)
            return steps if steps else None


def create_llm_client(config: AgentConfig) -> LLMClient:
    """Create and return an LLM client."""
    return LLMClient(config)