"""System prompts and templates for LLM interactions."""

# Base system prompt for the agent
SYSTEM_PROMPT = """You are a local coding agent. You work only within the designated workspace.
Provide concise, safe, and accurate responses. When generating changes, use unified diff format.
Be minimal and focused on the task at hand."""

# File generation prompt
FILE_GENERATION_PROMPT = """Convert the following description into an executable file.
Keep the structure simple and minimal. Only provide the file content, no explanations."""

# File editing prompt
FILE_EDIT_PROMPT = """Modify only the necessary parts of the file.
Output the changes as a unified diff patch. Be minimal and precise."""

# Multi-file patch prompt
MULTI_FILE_PATCH_PROMPT = """Generate unified diff patches for multiple files.
Use relative paths from the project root. Each file should have its own hunk."""

# Code analysis prompt
CODE_ANALYSIS_PROMPT = """Analyze the codebase and provide a structured overview.
Include file sizes, languages, and extract Python symbols (classes, functions, docstrings)."""

# Planning prompt
PLANNING_PROMPT = """Break down the goal into clear, actionable steps.
Return a JSON array of strings, each representing one step. Be concise and practical."""

# Safety warning messages
SAFETY_WARNINGS = {
    "delete": "⚠️  This will permanently delete: {path}",
    "overwrite": "⚠️  This will overwrite existing file: {path}",
    "patch": "⚠️  This will modify the following files: {files}",
}

# Success messages
SUCCESS_MESSAGES = {
    "file_created": "✅ Created file: {path}",
    "file_updated": "✅ Updated file: {path}",
    "file_deleted": "✅ Deleted: {path}",
    "command_executed": "✅ Command executed successfully",
    "patch_applied": "✅ Patch applied successfully",
    "todo_added": "✅ Added TODO item #{id}",
    "todo_completed": "✅ Marked TODO #{id} as done",
}

# Error messages
ERROR_MESSAGES = {
    "file_not_found": "❌ File not found: {path}",
    "permission_denied": "❌ Permission denied: {path}",
    "invalid_patch": "❌ Invalid patch format",
    "command_failed": "❌ Command failed with exit code: {code}",
    "llm_error": "❌ LLM API error: {error}",
    "config_error": "❌ Configuration error: {error}",
}