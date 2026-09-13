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
    """Formats standardized, cross-AI context payloads adhering to Section 8 schema."""

    @staticmethod
    def format_payload(context: Dict[str, Any], project_name: str, custom_instructions: Optional[str] = None) -> str:
        version = context.get("version", "v1.0")
        goal = context.get("objective") or "Develop and refine project features."
        current_state = context.get("current_state") or "In active development."

        # Requirements & Constraints
        reqs = context.get("requirements", [])
        consts = context.get("constraints", [])
        combined_reqs = reqs + [f"[Constraint] {c}" for c in consts]
        reqs_md = "\n".join(f"- {r}" for r in combined_reqs) if combined_reqs else "- Continue according to standard engineering best practices."

        # Decisions
        decs = context.get("decisions", []) + context.get("design_decisions", [])
        decs_md = "\n".join(f"- {d}" for d in decs) if decs else "- No conflicting architectural decisions recorded."

        # Completed Work
        completed = context.get("completed_work", [])
        completed_md = "\n".join(f"- {c}" for c in completed) if completed else "- Initial setup and baseline configuration completed."

        # Problems / Unresolved Issues / Failed attempts
        problems = context.get("open_problems", []) + context.get("errors", [])
        failed = context.get("failed_attempts", [])
        combined_issues = problems + [f"[Do Not Repeat] {f}" for f in failed]
        issues_md = "\n".join(f"- {p}" for p in combined_issues) if combined_issues else "- No active blockers or unresolved errors."

        # Files / Code context
        files = context.get("files_context", [])
        files_md = "\n".join(f"- `{f}`" for f in files) if files else "- Project root repository files."

        # Next steps
        next_steps = context.get("next_steps", [])
        next_md = "\n".join(f"{i+1}. {s}" for i, s in enumerate(next_steps)) if next_steps else "1. Review current state and proceed with next planned task."

        custom_directive = f"\n\n## Custom directive\n{custom_instructions}" if custom_instructions else ""

        return f"""# Continue this project

## Project
{project_name} ({version})

## Goal
{goal}

## Current state
{current_state}

## Important requirements
{reqs_md}

## Decisions already made
{decs_md}

## Completed work
{completed_md}

## Problems / unresolved issues
{issues_md}

## Important files or code context
{files_md}

## Next step
{next_md}
{custom_directive}
## Instructions for continuing
You are continuing this project directly from the CURRENT STATE above.
Do not restart from scratch, do not ask the user to re-explain, and do not repeat completed work or failed attempts.
Acknowledge receipt and proceed directly with Next Step 1."""

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
