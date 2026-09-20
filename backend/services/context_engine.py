"""
CONTINUO — Core Context Extraction Engine
Transforms noisy conversational transcripts into structured, provider-neutral Project Context Packages.

Continuo Philosophy:
Don't transfer the conversation transcript. Transfer what the next AI actually needs to proceed.
"""

import re
from typing import Dict, List, Any, Optional

class ContextEngine:
    """
    Intelligent extraction engine that parses AI interaction transcripts
    (ChatGPT, Claude, Gemini, Cursor) into structured, high-fidelity project packages.
    """

    @classmethod
    def extract(cls, raw_text: str, project_name: Optional[str] = None) -> Dict[str, Any]:
        """Parse dialogue and synthesize a structured context package."""
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        text_lower = raw_text.lower()

        # 1. Extract Objective
        objective = cls._extract_objective(lines, raw_text, project_name)

        # 2. Extract Requirements
        requirements = cls._extract_requirements(lines, raw_text)

        # 3. Extract Constraints
        constraints = cls._extract_constraints(lines, raw_text)

        # 4. Extract Critical Instructions
        instructions = cls._extract_instructions(lines, raw_text)

        # 5. Extract Decisions Made
        decisions = cls._extract_decisions(lines, raw_text)

        # 6. Extract Current State
        current_state = cls._extract_current_state(lines, raw_text, objective)

        # 7. Extract Completed Work
        completed_work = cls._extract_completed_work(lines, raw_text)

        # 8. Extract Pending Work
        pending_work = cls._extract_pending_work(lines, raw_text)

        # 9. Extract Open Problems & Bugs
        open_problems = cls._extract_open_problems(lines, raw_text)

        # 10. Extract Errors Encountered
        errors = cls._extract_errors(lines, raw_text)

        # 11. Extract Failed Approaches / Discarded Paths
        failed_attempts = cls._extract_failed_attempts(lines, raw_text)

        # 12. Extract File Paths & Code Context
        files_context = cls._extract_files(raw_text)

        # 13. Extract Design Decisions
        design_decisions = cls._extract_design_decisions(lines, raw_text)

        # 14. Extract Tech Stack & Dependencies
        dependencies = cls._extract_dependencies(raw_text)

        # 15. Extract Immediate Next Steps
        next_steps = cls._extract_next_steps(lines, raw_text, pending_work)

        return {
            "objective": objective,
            "requirements": requirements,
            "constraints": constraints,
            "instructions": instructions,
            "decisions": decisions,
            "current_state": current_state,
            "completed_work": completed_work,
            "pending_work": pending_work,
            "open_problems": open_problems,
            "errors": errors,
            "failed_attempts": failed_attempts,
            "files_context": files_context,
            "design_decisions": design_decisions,
            "dependencies": dependencies,
            "next_steps": next_steps,
        }

    @classmethod
    def _extract_objective(cls, lines: List[str], raw_text: str, project_name: Optional[str]) -> str:
        # Check explicit goal markers
        goal_matches = re.findall(
            r'(?:goal|objective|aim|purpose|building|building a|create a|implement a|project:?)\s*[:\-]\s*([^\.\n]+)',
            raw_text,
            re.IGNORECASE
        )
        if goal_matches:
            return goal_matches[0].strip().capitalize()

        # Look at the first user prompt statement
        for line in lines[:8]:
            if line.startswith(("#", "I want", "We need", "Build", "Create", "Please help")):
                clean = re.sub(r'^[#\s\-*]+', '', line).strip()
                if len(clean) > 12:
                    return clean

        name = project_name or "Project"
        return f"Build and deploy {name} production features with verified reliability."

    @classmethod
    def _extract_requirements(cls, lines: List[str], raw_text: str) -> List[str]:
        reqs = []
        pattern = re.compile(
            r'(?:must|need to|should|feature|require|requirement|deliverable|support|allow users? to)\s+([^.\n]+)',
            re.IGNORECASE
        )
        for line in lines:
            if any(k in line.lower() for k in ["requirement", "feature:", "needs to", "must support"]):
                clean = re.sub(r'^[0-9\.\-\*\s#]+', '', line).strip()
                if 10 < len(clean) < 140 and clean not in reqs:
                    reqs.append(clean)
            else:
                for match in pattern.findall(line):
                    clean = match.strip()
                    if 10 < len(clean) < 120 and clean not in reqs:
                        reqs.append(clean.capitalize())

        if not reqs:
            reqs = [
                "Implement end-to-end functionality according to technical specification",
                "Maintain complete test coverage across core pathways",
                "Ensure backward compatibility and clean error boundaries"
            ]
        return reqs[:8]

    @classmethod
    def _extract_constraints(cls, lines: List[str], raw_text: str) -> List[str]:
        constraints = []
        for line in lines:
            lower = line.lower()
            if any(k in lower for k in ["do not", "never", "cannot", "must not", "avoid", "don't", "constraint"]):
                clean = re.sub(r'^[0-9\.\-\*\s#]+', '', line).strip()
                if 10 < len(clean) < 140 and clean not in constraints:
                    constraints.append(clean)

        if not constraints:
            constraints = [
                "Do not introduce breaking changes to existing interface contracts",
                "Never commit unencrypted secrets or credentials to source control",
                "Maintain zero-crash resilience on boundary conditions"
            ]
        return constraints[:6]

    @classmethod
    def _extract_instructions(cls, lines: List[str], raw_text: str) -> List[str]:
        instructions = []
        for line in lines:
            lower = line.lower()
            if any(k in lower for k in ["always", "keep in mind", "remember", "strictly", "note that", "ensure that"]):
                clean = re.sub(r'^[0-9\.\-\*\s#]+', '', line).strip()
                if 10 < len(clean) < 130 and clean not in instructions:
                    instructions.append(clean)
        return instructions[:6]

    @classmethod
    def _extract_decisions(cls, lines: List[str], raw_text: str) -> List[str]:
        decisions = []
        for line in lines:
            lower = line.lower()
            if any(k in lower for k in ["decided", "chosen", "agreed", "selected", "switched to", "going with", "opted for"]):
                clean = re.sub(r'^[0-9\.\-\*\s#]+', '', line).strip()
                if 10 < len(clean) < 140 and clean not in decisions:
                    decisions.append(clean)

        if not decisions:
            decisions = [
                "Adopted modular architecture separating context extraction from provider transport",
                "Standardized on structured JSON packages for cross-model portability"
            ]
        return decisions[:7]

    @classmethod
    def _extract_current_state(cls, lines: List[str], raw_text: str, objective: str) -> str:
        state_markers = re.findall(
            r'(?:current state|currently|status:?|working state|we are at)\s*[:\-]\s*([^\.\n]+)',
            raw_text,
            re.IGNORECASE
        )
        if state_markers:
            return state_markers[0].strip().capitalize()
        return f"Active development underway. Foundation established; iterating on core pipeline for {objective}."

    @classmethod
    def _extract_completed_work(cls, lines: List[str], raw_text: str) -> List[str]:
        done = []
        for line in lines:
            lower = line.lower()
            if any(k in lower for k in ["completed", "implemented", "finished", "[x]", "done:", "fixed:"]):
                clean = re.sub(r'^[0-9\.\-\*\[\]xX\s#]+', '', line).strip()
                if 8 < len(clean) < 130 and clean not in done:
                    done.append(clean)
        if not done:
            done = [
                "Initial project configuration and environment variables verified",
                "Core schema definitions and persistence models implemented"
            ]
        return done[:7]

    @classmethod
    def _extract_pending_work(cls, lines: List[str], raw_text: str) -> List[str]:
        pending = []
        for line in lines:
            lower = line.lower()
            if any(k in lower for k in ["pending", "todo", "still need", "remaining", "[ ]", "to do"]):
                clean = re.sub(r'^[0-9\.\-\*\[\]\s#]+', '', line).strip()
                if 8 < len(clean) < 130 and clean not in pending:
                    pending.append(clean)
        if not pending:
            pending = [
                "Complete automated end-to-end regression test suite",
                "Perform cross-browser verification and token handoff sanity checks"
            ]
        return pending[:6]

    @classmethod
    def _extract_open_problems(cls, lines: List[str], raw_text: str) -> List[str]:
        problems = []
        for line in lines:
            lower = line.lower()
            if any(k in lower for k in ["problem:", "issue:", "bug:", "failing", "unresolved", "bottleneck"]):
                clean = re.sub(r'^[0-9\.\-\*\s#]+', '', line).strip()
                if 10 < len(clean) < 140 and clean not in problems:
                    problems.append(clean)
        return problems[:5]

    @classmethod
    def _extract_errors(cls, lines: List[str], raw_text: str) -> List[str]:
        errors = []
        for line in lines:
            if any(k in line for k in ["Error:", "Exception:", "HTTP 5", "HTTP 4", "Failed with", "Traceback"]):
                clean = re.sub(r'^[0-9\.\-\*\s#]+', '', line).strip()
                if 10 < len(clean) < 150 and clean not in errors:
                    errors.append(clean)
        return errors[:4]

    @classmethod
    def _extract_failed_attempts(cls, lines: List[str], raw_text: str) -> List[str]:
        failed = []
        for line in lines:
            lower = line.lower()
            if any(k in lower for k in ["tried", "failed attempt", "discarded", "rejected approach", "did not work", "reverted"]):
                clean = re.sub(r'^[0-9\.\-\*\s#]+', '', line).strip()
                if 10 < len(clean) < 140 and clean not in failed:
                    failed.append(clean)
        return failed[:4]

    @classmethod
    def _extract_files(cls, raw_text: str) -> List[str]:
        # Regex for filenames and paths (e.g. app.py, src/main.ts, styles.css)
        file_matches = re.findall(
            r'(?:[\w\.\-/]+\.(?:py|js|ts|tsx|jsx|css|html|json|sql|sh|yaml|yml|md|env))',
            raw_text
        )
        unique_files = []
        for f in file_matches:
            if len(f) > 3 and not f.startswith("http") and f not in unique_files:
                unique_files.append(f)
        return unique_files[:10]

    @classmethod
    def _extract_design_decisions(cls, lines: List[str], raw_text: str) -> List[str]:
        design = []
        keywords = ["glass", "blur", "ui", "ux", "dark mode", "font", "typography", "palette", "mobile", "animation"]
        for line in lines:
            lower = line.lower()
            if any(k in lower for k in keywords) and len(line) < 120:
                clean = re.sub(r'^[0-9\.\-\*\s#]+', '', line).strip()
                if clean and clean not in design:
                    design.append(clean)
        return design[:5]

    @classmethod
    def _extract_dependencies(cls, raw_text: str) -> List[str]:
        known_deps = [
            "FastAPI", "Python", "SQLAlchemy", "PostgreSQL", "SQLite", "Supabase",
            "Next.js", "React", "TypeScript", "Tailwind CSS", "Pytest", "Uvicorn",
            "PyJWT", "Pydantic", "Chrome MV3"
        ]
        found = []
        text_lower = raw_text.lower()
        for dep in known_deps:
            if dep.lower() in text_lower and dep not in found:
                found.append(dep)
        return found

    @classmethod
    def _extract_next_steps(cls, lines: List[str], raw_text: str, pending_work: List[str]) -> List[str]:
        next_steps = []
        for line in lines:
            lower = line.lower()
            if any(k in lower for k in ["next step", "next:", "step 1", "step 2", "proceed to", "then we will"]):
                clean = re.sub(r'^[0-9\.\-\*\s#]+', '', line).strip()
                if 10 < len(clean) < 130 and clean not in next_steps:
                    next_steps.append(clean)

        if not next_steps:
            next_steps = pending_work[:3] if pending_work else [
                "Validate model handoff payload in target environment",
                "Execute test suite to confirm operational parity"
            ]
        return next_steps[:5]

    @classmethod
    def extract_context_os(
        cls,
        raw_text: str,
        project_name: Optional[str] = None,
        project_id: Optional[str] = None,
        current_user_id: Optional[str] = None,
        db: Optional[Any] = None,
        session_id: Optional[str] = None,
    ):
        """
        Phase 9.5: Extract structured Context OS entities (Goals, Decisions, Tasks,
        Technical States, Design Context, Visual References) from raw transcript.
        """
        from backend.services.context_extraction import ContextExtractionService
        return ContextExtractionService.extract(
            raw_text=raw_text,
            project_name=project_name,
            project_id=project_id,
            current_user_id=current_user_id,
            db=db,
            session_id=session_id,
        )
