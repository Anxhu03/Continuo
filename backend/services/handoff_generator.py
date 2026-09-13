"""
CONTINUO — Cross-AI Model Handoff Dispatcher & Provider Abstraction
Generates provider-tailored context continuation packages for ChatGPT, Claude, Gemini, and Cursor.
Includes honest destination links and clipboard-ready continuation packages.
"""

from typing import Dict, Any, Optional

PROVIDER_URLS = {
    "chatgpt": "https://chatgpt.com/",
    "claude": "https://claude.ai/new",
    "gemini": "https://gemini.google.com/app",
    "cursor": "https://www.cursor.com/"
}

class BaseProviderAdapter:
    """Base class for AI Model Prompt Formatters."""
    name: str = "base"

    def format(self, context: Dict[str, Any], project_name: str, custom_instructions: Optional[str] = None) -> str:
        raise NotImplementedError

class UniversalHandoffFormatter:
    """Formats standardized, cross-AI context payloads adhering to token-efficient continuation schema."""

    @staticmethod
    def format_payload(context: Dict[str, Any], project_name: str, custom_instructions: Optional[str] = None) -> str:
        version = context.get("version", "v1.0")
        goal = context.get("objective") or "Develop and refine project features."
        current_state = context.get("current_state") or "In active development."

        # Completed
        completed = context.get("completed_work", [])
        completed_md = "\n".join(f"- {c}" for c in completed) if completed else "- Core baseline architecture established."

        # Important decisions
        decs = context.get("decisions", []) + context.get("design_decisions", [])
        decs_md = "\n".join(f"- {d}" for d in decs) if decs else "- Standard architectural patterns applied."

        # Constraints & Requirements
        consts = context.get("constraints", [])
        reqs = context.get("requirements", [])
        combined_consts = consts + reqs
        consts_md = "\n".join(f"- {c}" for c in combined_consts) if combined_consts else "- Follow standard engineering quality and security guidelines."

        # Known problems & unresolved issues
        problems = context.get("open_problems", []) + context.get("errors", [])
        failed = context.get("failed_attempts", [])
        combined_problems = problems + [f"[Do not repeat] {f}" for f in failed]
        problems_md = "\n".join(f"- {p}" for p in combined_problems) if combined_problems else "- None recorded."

        # Important files / code context
        files = context.get("files_context", [])
        files_md = f"\n\nFiles in scope:\n" + "\n".join(f"- `{f}`" for f in files) if files else ""

        # Next task / steps
        next_steps = context.get("next_steps", [])
        next_task = "\n".join(f"{i+1}. {s}" for i, s in enumerate(next_steps)) if next_steps else "1. Proceed with the next planned engineering milestone."

        custom_directive = f"\n\nDirective:\n{custom_instructions}" if custom_instructions else ""

        return f"""You are continuing an existing project.

Project:
{project_name} ({version})

Goal:
{goal}

Current state:
{current_state}

Completed:
{completed_md}

Important decisions:
{decs_md}

Constraints:
{consts_md}

Known problems:
{problems_md}{files_md}

Next task:
{next_task}{custom_directive}

Continue from the current state. Do not restart the project or repeat completed work."""

class ClaudeProviderAdapter(BaseProviderAdapter):
    """Formats context for Anthropic Claude models."""
    name: str = "claude"

    def format(self, context: Dict[str, Any], project_name: str, custom_instructions: Optional[str] = None) -> str:
        return UniversalHandoffFormatter.format_payload(context, project_name, custom_instructions)

class ChatGPTProviderAdapter(BaseProviderAdapter):
    """Formats context for OpenAI ChatGPT models."""
    name: str = "chatgpt"

    def format(self, context: Dict[str, Any], project_name: str, custom_instructions: Optional[str] = None) -> str:
        return UniversalHandoffFormatter.format_payload(context, project_name, custom_instructions)

class GeminiProviderAdapter(BaseProviderAdapter):
    """Formats context for Google Gemini models."""
    name: str = "gemini"

    def format(self, context: Dict[str, Any], project_name: str, custom_instructions: Optional[str] = None) -> str:
        return UniversalHandoffFormatter.format_payload(context, project_name, custom_instructions)

class CursorProviderAdapter(BaseProviderAdapter):
    """Formats context for Cursor Agentic IDE."""
    name: str = "cursor"

    def format(self, context: Dict[str, Any], project_name: str, custom_instructions: Optional[str] = None) -> str:
        files = "\n".join(f"- `{f}`" for f in context.get("files_context", []))
        decs = "\n".join(f"- {d}" for d in context.get("decisions", []))
        consts = "\n".join(f"- {c}" for c in context.get("constraints", []))
        next_s = "\n".join(f"{i+1}. {s}" for i, s in enumerate(context.get("next_steps", [])))

        return f"""/* CONTINUO CURSOR AGENT SPEC: {project_name} */
// Current State: {context.get('current_state', '')}
// Goal: {context.get('objective', '')}

### FILES IN SCOPE
{files}

### ARCHITECTURAL DECISIONS
{decs}

### CONSTRAINTS (DO NOT VIOLATE)
{consts}

### IMMEDIATE ACTION ITEMS
{next_s}
{f"// Directive: {custom_instructions}" if custom_instructions else ""}
"""

class HandoffService:
    """Universal dispatcher for generating cross-AI continuation payloads."""
    adapters = {
        "claude": ClaudeProviderAdapter(),
        "chatgpt": ChatGPTProviderAdapter(),
        "gemini": GeminiProviderAdapter(),
        "cursor": CursorProviderAdapter(),
    }

    @classmethod
    def generate(
        cls,
        context_data: Dict[str, Any],
        project_name: str,
        destination_provider: str = "claude",
        custom_instructions: Optional[str] = None
    ) -> Dict[str, str]:
        dest_key = destination_provider.lower().strip()
        adapter = cls.adapters.get(dest_key, cls.adapters["claude"])

        payload = adapter.format(context_data, project_name, custom_instructions)
        dest_url = PROVIDER_URLS.get(dest_key, "https://claude.ai/new")

        return {
            "formatted_payload": payload,
            "destination_url": dest_url,
            "provider": dest_key
        }
