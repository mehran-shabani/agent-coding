"""Base prompts for the Local Coding Agent."""

# System prompts
SYSTEM_PROMPT = """تو یک ایجنت کدنویسی لوکال هستی؛ فقط در workspace تعیین‌شده کار کن؛ تغییرات را به صورت unified diff ارائه بده؛ پاسخ‌ها کوتاه و ایمن باشند."""

FILE_GENERATION_PROMPT = """توضیح را به فایل اجرایی تبدیل کن؛ ساختار ساده و مینیمال باشد."""

FILE_EDIT_PROMPT = """فقط بخش‌های لازم تغییر کند؛ خروجی unified diff باشد."""

MULTI_FILE_PATCH_PROMPT = """پچ چندفایلی با مسیر نسبی از ریشهٔ پروژه بده؛ هر فایل در hunk جدا باشد."""

PLANNING_PROMPT = """یک برنامه‌ریز کدنویسی هستی. گام‌های عملی و قابل اجرا برای دستیابی به هدف ارائه بده."""

ANALYSIS_PROMPT = """یک تحلیلگر کد هستی. ساختار پروژه، فایل‌ها، کلاس‌ها و توابع را به صورت منظم تحلیل کن."""


def format_file_generation_prompt(description: str, file_path: str) -> str:
    """Format prompt for file generation."""
    return f"""Create a file at path '{file_path}' with the following description:

{description}

Generate only the file content, no explanations."""


def format_file_edit_prompt(file_content: str, file_path: str, instruction: str) -> str:
    """Format prompt for file editing."""
    return f"""File path: {file_path}

Current content:
```
{file_content}
```

Edit instruction: {instruction}

Generate a unified diff patch for the changes. Only output the diff, no explanations."""


def format_multi_file_patch_prompt(project_context: str, description: str) -> str:
    """Format prompt for multi-file patch generation."""
    return f"""Project context:
{project_context}

Changes needed:
{description}

Generate a unified diff patch for multiple files. Use relative paths from project root."""


def format_planning_prompt(goal: str, context: str = None) -> str:
    """Format prompt for plan creation."""
    prompt = f"""Create a step-by-step plan to achieve this goal: {goal}

Return the plan as a JSON array of strings, where each string is a task step. Only return the JSON, no explanations."""
    
    if context:
        prompt = f"""Project context: {context}

{prompt}"""
    
    return prompt


def format_analysis_prompt(directory_path: str, file_list: list) -> str:
    """Format prompt for project analysis."""
    files_text = "\n".join([f"- {f}" for f in file_list])
    
    return f"""Analyze this project structure and generate a comprehensive code map.

Directory: {directory_path}

Files found:
{files_text}

Create a structured analysis including:
1. Project overview
2. File organization
3. Programming languages used
4. Key components and their purposes
5. Dependencies and relationships

Format the output as a well-structured Markdown document."""


def format_question_prompt(question: str, context: str = None) -> str:
    """Format prompt for general questions."""
    if context:
        return f"""Context: {context}

Question: {question}"""
    
    return question