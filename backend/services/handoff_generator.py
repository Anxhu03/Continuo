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

class ClaudeProviderAdapter(BaseProviderAdapter):
    """Formats context using Anthropic Claude XML tags for zero-hallucination continuation."""
    name: str = "claude"

    def format(self, context: Dict[str, Any], project_name: str, custom_instructions: Optional[str] = None) -> str:
        reqs = "\n".join(f"  - {r}" for r in context.get("requirements", []))
        consts = "\n".join(f"  - {c}" for c in context.get("constraints", []))
        decs = "\n".join(f"  - {d}" for d in context.get("decisions", []))
        done = "\n".join(f"  - {w}" for w in context.get("completed_work", []))
        pending = "\n".join(f"  - {p}" for p in context.get("pending_work", []))
        failed = "\n".join(f"  - {f}" for f in context.get("failed_attempts", []))
        files = ", ".join(context.get("files_context", [])) or "None specified"
        next_steps = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(context.get("next_steps", [])))

        return f"""<project_context platform="Continuo" project="{project_name}" version="{context.get('version', 'v1.0')}">
<instruction>
You are continuing development on project "{project_name}".
Do not restart from scratch. Pick up directly from the verified current state below.
</instruction>

<objective>
{context.get('objective', '')}
</objective>

<current_state>
{context.get('current_state', '')}
</current_state>

<verified_decisions>
{decs}
</verified_decisions>

<hard_constraints>
{consts}
</hard_constraints>

<active_requirements>
{reqs}
</active_requirements>

<completed_work>
{done}
</completed_work>

<pending_work>
{pending}
</pending_work>

<failed_attempts_do_not_repeat>
{failed}
</failed_attempts_do_not_repeat>

<files_in_scope>
{files}
</files_in_scope>

<immediate_next_steps>
{next_steps}
</immediate_next_steps>
{f"<custom_directive>{custom_instructions}</custom_directive>" if custom_instructions else ""}
</project_context>

Please acknowledge current state v{context.get('version', 'v1.0')} and immediately proceed with Step 1 of the immediate next steps."""

class ChatGPTProviderAdapter(BaseProviderAdapter):
    """Formats context for OpenAI ChatGPT models (markdown headers + bulleted instructions)."""
    name: str = "chatgpt"

    def format(self, context: Dict[str, Any], project_name: str, custom_instructions: Optional[str] = None) -> str:
        reqs = "\n".join(f"- {r}" for r in context.get("requirements", []))
        consts = "\n".join(f"- {c}" for c in context.get("constraints", []))
        decs = "\n".join(f"- {d}" for d in context.get("decisions", []))
        pending = "\n".join(f"- {p}" for p in context.get("pending_work", []))
        files = ", ".join(context.get("files_context", [])) or "N/A"
        next_steps = "\n".join(f"{i+1}. {s}" for i, s in enumerate(context.get("next_steps", [])))

        return f"""# CONTINUO CONTEXT PACKAGE: {project_name.upper()} (v{context.get('version', 'v1.0')})

> **SYSTEM INSTRUCTION**: You are continuing an existing project. Read the current state and constraints carefully. Do NOT re-explain or restart. Continue from the current state.

## 1. Project Objective
{context.get('objective', '')}

## 2. Current State
{context.get('current_state', '')}

## 3. Established Architectural Decisions
{decs}

## 4. Non-Negotiable Constraints
{consts}

## 5. Active Requirements
{reqs}

## 6. Pending Work & Files in Scope
- Files: {files}
{pending}

## 7. Immediate Next Steps
{next_steps}
{f"**Directive**: {custom_instructions}" if custom_instructions else ""}

Confirm you have ingested this context and tell me your specific action plan for Step 1."""

class GeminiProviderAdapter(BaseProviderAdapter):
    """Formats context for Google Gemini 2.0."""
    name: str = "gemini"

    def format(self, context: Dict[str, Any], project_name: str, custom_instructions: Optional[str] = None) -> str:
        return ChatGPTProviderAdapter().format(context, project_name, custom_instructions)

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
