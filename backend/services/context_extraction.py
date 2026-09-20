"""
CONTINUO — Context Extraction Intelligence Service (Phase 9.5)
Transforms conversation transcripts into structured, persistent Context OS entities:
Goals, Decisions, Tasks, Technical States, Design Context, and Visual References.
Provides deterministic confidence classification, contradiction detection,
secret sanitization, deduplication, and secure visual asset association.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session

from backend.models import (
    User,
    Project,
    ContextGoal,
    ContextDecision,
    ContextTask,
    ContextTechnicalState,
    ContextImage,
    Conversation,
    utc_now,
)
from backend.schemas import (
    ExtractedGoalCandidate,
    ExtractedDecisionCandidate,
    ExtractedTaskCandidate,
    ExtractedTechStateCandidate,
    ExtractedVisualReferenceCandidate,
    StructuredExtractionResult,
    ContradictionItem,
)
from backend.services.handoff_generator import sanitize_secrets
from backend.services.contradiction import ContradictionDetector, MUTUALLY_EXCLUSIVE_GROUPS


class ContextExtractionService:
    """
    Core service for extracting and persisting normalized Context OS entities
    from conversational interaction transcripts.
    """

    # Tentative markers that downgrade confidence and classify decisions as 'under_review'
    TENTATIVE_PATTERNS = [
        r'\bmaybe\b',
        r'\bperhaps\b',
        r'\bcould we\b',
        r'\bwe could\b',
        r'\bmight\b',
        r'\bi think we (?:should|could)\b',
        r'\bwhat if we\b',
        r'\bwe might consider\b',
        r'\bconsidering\b',
        r'\bpossible approach\b',
        r'\boptionally\b',
        r'\bi like this\b',
    ]

    # Explicit decision markers
    EXPLICIT_DECISION_PATTERNS = [
        r'(?:we have decided|we decided|decided to|decision:?|chosen:?|selected:?|agreed to|going with|opted for|switched to|standardized on)\s+([^\.\n]+)',
        r'(?:we will use|we shall use|let us use|let\'s use|use)\s+([A-Z][a-zA-Z0-9_\-\.\+]+(?:\s+[A-Z][a-zA-Z0-9_\-\.\+]+)*)',
    ]

    # Visual reference patterns
    VISUAL_CUES = {
        "character_reference": [
            r'\bcharacter\b', r'\bavatar\b', r'\bmascot\b', r'\b3d model\b', r'\bglb\b', r'\bgltf\b'
        ],
        "ui_screenshot": [
            r'\bbug\b', r'\bissue\b', r'\berror screenshot\b', r'\bbroken ui\b', r'\bshows the problem\b',
            r'\bui screenshot\b', r'\bscreenshot shows\b', r'\bfailing screen\b'
        ],
        "design_reference": [
            r'\blook like this\b', r'\bmake (?:it|my) (?:portfolio|app|site|ui) look like\b',
            r'\bdesign reference\b', r'\baesthetic\b', r'\bvisual reference\b', r'\binspiration\b',
            r'\bminimal layout\b', r'\bdark glass\b'
        ],
        "blender_render": [
            r'\bblender\b', r'\brender\b', r'\bcycles\b', r'\beevee\b'
        ],
        "diagram": [
            r'\bdiagram\b', r'\bflowchart\b', r'\barchitecture diagram\b', r'\bschema diagram\b'
        ],
        "before_after": [
            r'\bbefore and after\b', r'\bbefore\/after\b', r'\bcomparison screenshot\b'
        ],
        "moodboard": [
            r'\bmoodboard\b', r'\bmood board\b', r'\bpalette\b'
        ],
    }

    @classmethod
    def extract(
        cls,
        raw_text: str,
        project_name: Optional[str] = None,
        project_id: Optional[str] = None,
        current_user_id: Optional[str] = None,
        db: Optional[Session] = None,
        session_id: Optional[str] = None,
    ) -> StructuredExtractionResult:
        """
        Extract structured Context OS candidates from raw conversational transcript.
        Completely deterministic, offline-capable, and requires zero external vision APIs.
        """
        if not raw_text or not raw_text.strip():
            return StructuredExtractionResult(
                goals=[],
                decisions=[],
                tasks=[],
                technical_states=[],
                visual_references=[],
                design_context=[],
                project_state="No active context recorded in empty conversation.",
                confidence_summary={"overall": 0.0},
                contradictions=[]
            )

        # Sanitize transcript first to prevent credentials from propagating
        cleaned_text = sanitize_secrets(raw_text)
        # Normalize text to split when directives/statements are concatenated on the same line
        normalized_text = re.sub(
            r'(?<=[.!?])\s+(?=(?:decision|todo|task|completed|fixed|done|requirement|constraint|goal|objective|status|pending|current state)[:\s])',
            '\n',
            cleaned_text,
            flags=re.IGNORECASE
        )
        lines = [line.strip() for line in normalized_text.splitlines() if line.strip()]

        # 1. Extract Goals (Goals, Requirements, Constraints, Instructions)
        goals = cls._extract_goals(lines, cleaned_text, project_name)

        # 2. Extract Decisions (with confidence classification & tentative detection)
        decisions = cls._extract_decisions(lines, cleaned_text)

        # 3. Extract Tasks (todos, completed, in-progress)
        tasks = cls._extract_tasks(lines, cleaned_text)

        # 4. Extract Technical States (frameworks, runtimes, renderer, DBs)
        tech_states = cls._extract_technical_states(lines, cleaned_text)

        # 5. Extract Design Context
        design_context = cls._extract_design_context(lines, cleaned_text)

        # 6. Extract Project State
        project_state = cls._extract_project_state(lines, cleaned_text)

        # 7. Extract Visual References & Image Associations
        visual_refs = cls._extract_visual_references(
            lines, cleaned_text, project_id, current_user_id, db, session_id, goals, decisions, tasks
        )

        # 8. Contradiction Detection
        contradictions = cls._detect_contradictions(decisions, goals, project_id, db)

        # 9. Confidence Summary
        all_confidences = (
            [g.confidence for g in goals] +
            [d.confidence for d in decisions] +
            [t.confidence for t in tasks] +
            [s.confidence for s in tech_states] +
            [v.confidence for v in visual_refs]
        )
        avg_confidence = round(sum(all_confidences) / len(all_confidences), 2) if all_confidences else 0.85
        confidence_summary = {
            "overall": avg_confidence,
            "goals_confidence": round(sum(g.confidence for g in goals) / len(goals), 2) if goals else 0.9,
            "decisions_confidence": round(sum(d.confidence for d in decisions) / len(decisions), 2) if decisions else 0.9,
            "tasks_confidence": round(sum(t.confidence for t in tasks) / len(tasks), 2) if tasks else 0.9,
        }

        return StructuredExtractionResult(
            goals=goals,
            decisions=decisions,
            tasks=tasks,
            technical_states=tech_states,
            visual_references=visual_refs,
            design_context=design_context,
            project_state=project_state,
            confidence_summary=confidence_summary,
            contradictions=contradictions
        )

    # =========================================================================
    # GOAL EXTRACTION
    # =========================================================================

    @classmethod
    def _extract_goals(
        cls, lines: List[str], raw_text: str, project_name: Optional[str]
    ) -> List[ExtractedGoalCandidate]:
        candidates: List[ExtractedGoalCandidate] = []
        seen_titles = set()

        def add_candidate(title: str, category: str, priority: str, confidence: float, explicit: bool, desc: Optional[str] = None):
            title = sanitize_secrets(title).strip()
            title = re.sub(r'^[0-9\.\-\*\s#:]+', '', title).strip()
            if not title or len(title) < 5:
                return
            norm = re.sub(r'[^a-z0-9]', '', title.lower())
            if norm in seen_titles:
                return
            seen_titles.add(norm)
            candidates.append(
                ExtractedGoalCandidate(
                    title=title[:250],
                    description=sanitize_secrets(desc) if desc else None,
                    category=category,
                    priority=priority,
                    confidence=confidence,
                    explicit=explicit,
                )
            )

        # Primary Objective / Goal
        goal_matches = re.findall(
            r'(?:goal|objective|aim|purpose|building|building a|create a|implement a|project:?)\s*[:\-]\s*([^\.\n]+)',
            raw_text,
            re.IGNORECASE
        )
        if goal_matches:
            for gm in goal_matches[:2]:
                add_candidate(gm.strip().capitalize(), category="goal", priority="high", confidence=0.95, explicit=True)

        for line in lines[:8]:
            clean_line = re.sub(r'^(?:user|human|assistant|ai|prompt|client)[:\s]+', '', line, flags=re.IGNORECASE).strip()
            if any(clean_line.lower().startswith(p) for p in ["i want to build", "we need to build", "build a", "create a", "i want to create", "i want to"]):
                clean = re.sub(r'^[#\s\-*]+', '', clean_line).strip()
                if len(clean) > 10:
                    add_candidate(clean.capitalize(), category="goal", priority="high", confidence=0.90, explicit=True)
                    break

        # Requirements
        for line in lines:
            clean_line = re.sub(r'^(?:user|human|assistant|ai|prompt|client)[:\s]+', '', line, flags=re.IGNORECASE).strip()
            line_low = clean_line.lower()
            if line_low.startswith(("requirement:", "req:", "- requirement")):
                val = re.sub(r'^(?:requirement|req)[:\s\-*]+', '', clean_line, flags=re.IGNORECASE).strip()
                add_candidate(val, category="requirement", priority="normal", confidence=0.92, explicit=True)
            elif any(k in line_low for k in ["must support", "must integrate", "needs to support", "needs to provide"]):
                add_candidate(clean_line, category="requirement", priority="high", confidence=0.88, explicit=True)

        # Constraints
        for line in lines:
            clean_line = re.sub(r'^(?:user|human|assistant|ai|prompt|client)[:\s]+', '', line, flags=re.IGNORECASE).strip()
            line_low = clean_line.lower()
            if line_low.startswith(("constraint:", "- constraint")):
                val = re.sub(r'^(?:constraint)[:\s\-*]+', '', clean_line, flags=re.IGNORECASE).strip()
                add_candidate(val, category="constraint", priority="critical", confidence=0.95, explicit=True)
            elif any(k in line_low for k in ["do not use", "never use", "cannot use", "must not", "strictly prohibit"]):
                add_candidate(clean_line, category="constraint", priority="critical", confidence=0.90, explicit=True)

        return candidates

    # =========================================================================
    # DECISION EXTRACTION
    # =========================================================================

    @classmethod
    def _extract_decisions(cls, lines: List[str], raw_text: str) -> List[ExtractedDecisionCandidate]:
        candidates: List[ExtractedDecisionCandidate] = []
        seen_titles = set()

        def add_decision(title: str, category: str, status: str, confidence: float, explicit: bool, rationale: Optional[str] = None):
            title = sanitize_secrets(title).strip()
            title = re.sub(r'^[0-9\.\-\*\s#:]+', '', title).strip()
            if not title or len(title) < 5:
                return
            norm = re.sub(r'[^a-z0-9]', '', title.lower())
            if norm in seen_titles:
                return
            seen_titles.add(norm)
            candidates.append(
                ExtractedDecisionCandidate(
                    title=title[:250],
                    category=category,
                    status=status,
                    confidence=confidence,
                    explicit=explicit,
                    rationale=sanitize_secrets(rationale) if rationale else None,
                )
            )

        for line in lines:
            line_low = line.lower()

            # Check for tentative / ambiguous language
            is_tentative = any(re.search(p, line_low) for p in cls.TENTATIVE_PATTERNS)

            # Explicit Decision line markers
            if line_low.startswith(("decision:", "- decision", "agreed:", "chosen:")):
                val = re.sub(r'^(?:decision|agreed|chosen)[:\s\-*]+', '', line, flags=re.IGNORECASE).strip()
                cat = cls._categorize_decision(val)
                if is_tentative:
                    add_decision(val, category=cat, status="under_review", confidence=0.45, explicit=False)
                else:
                    add_decision(val, category=cat, status="accepted", confidence=0.95, explicit=True)
                continue

            # Check verbal explicit patterns
            matched_explicit = False
            for pat in cls.EXPLICIT_DECISION_PATTERNS:
                m = re.search(pat, line, re.IGNORECASE)
                if m:
                    match_str = line.strip()
                    cat = cls._categorize_decision(match_str)
                    if is_tentative:
                        add_decision(match_str, category=cat, status="under_review", confidence=0.48, explicit=False)
                    else:
                        add_decision(match_str, category=cat, status="accepted", confidence=0.92, explicit=True)
                    matched_explicit = True
                    break

            if matched_explicit:
                continue

            # Tentative mentions without explicit markers (e.g. "Maybe we should use Three.js", "I like this design")
            if is_tentative:
                if any(tech in line_low for tech in ["three.js", "babylon", "react", "fastapi", "vue", "tailwind", "design", "glass"]):
                    cat = cls._categorize_decision(line)
                    add_decision(line, category=cat, status="under_review", confidence=0.42, explicit=False)

        return candidates

    @classmethod
    def _categorize_decision(cls, text: str) -> str:
        text_low = text.lower()
        if any(w in text_low for w in ["database", "postgres", "sql", "sqlite", "redis", "mongodb"]):
            return "database"
        if any(w in text_low for w in ["design", "glass", "theme", "layout", "aesthetic", "css", "color", "font"]):
            return "design_system"
        if any(w in text_low for w in ["three.js", "babylon", "renderer", "webgl", "canvas", "3d"]):
            return "renderer"
        if any(w in text_low for w in ["react", "vue", "next.js", "frontend", "svelte", "ui"]):
            return "frontend"
        if any(w in text_low for w in ["fastapi", "django", "flask", "backend", "api"]):
            return "backend"
        return "architecture"

    # =========================================================================
    # TASK EXTRACTION
    # =========================================================================

    @classmethod
    def _extract_tasks(cls, lines: List[str], raw_text: str) -> List[ExtractedTaskCandidate]:
        candidates: List[ExtractedTaskCandidate] = []
        seen = set()

        for line in lines:
            clean_line = re.sub(r'^(?:user|human|assistant|ai|prompt|client)[:\s]+', '', line, flags=re.IGNORECASE).strip()
            line_low = clean_line.lower()
            status = "todo"
            priority = "normal"

            # Check if line indicates completed task
            if any(line_low.startswith(p) for p in ["completed:", "done:", "fixed:", "[x]"]):
                status = "completed"
                clean = re.sub(r'^(?:completed|done|fixed|\[x\])[:\s\-*]+', '', clean_line, flags=re.IGNORECASE).strip()
            elif any(line_low.startswith(p) for p in ["pending:", "todo:", "task:", "[ ]", "next step:"]):
                clean = re.sub(r'^(?:pending|todo|task|\[\s\]|next step)[:\s\-*]+', '', clean_line, flags=re.IGNORECASE).strip()
            elif any(k in line_low for k in ["fix the", "implement the", "create the", "update the", "integrate the"]):
                clean = clean_line.strip()
                if any(w in line_low for w in ["urgent", "critical", "crash", "bug"]):
                    priority = "high"
            else:
                continue

            clean = sanitize_secrets(clean)
            clean = re.sub(r'^[0-9\.\-\*\s#:]+', '', clean).strip()
            if not clean or len(clean) < 6:
                continue
            norm = re.sub(r'[^a-z0-9]', '', clean.lower())
            if norm in seen:
                continue
            seen.add(norm)

            candidates.append(
                ExtractedTaskCandidate(
                    title=clean[:250],
                    status=status,
                    priority=priority,
                    confidence=0.90,
                    explicit=True,
                )
            )

        return candidates

    # =========================================================================
    # TECHNICAL STATE EXTRACTION
    # =========================================================================

    @classmethod
    def _extract_technical_states(cls, lines: List[str], raw_text: str) -> List[ExtractedTechStateCandidate]:
        candidates: List[ExtractedTechStateCandidate] = []
        seen = set()
        text_low = raw_text.lower()

        def add_state(cat: str, key: str, val: str, conf: float = 0.9, explicit: bool = True):
            k_tuple = (cat.lower(), key.lower())
            if k_tuple in seen:
                return
            seen.add(k_tuple)
            candidates.append(
                ExtractedTechStateCandidate(
                    category=cat,
                    key=key,
                    value=sanitize_secrets(val),
                    confidence=conf,
                    explicit=explicit
                )
            )

        # 3D Renderer detection
        if "three.js" in text_low or "threejs" in text_low:
            add_state("renderer", "3d_engine", "Three.js", conf=0.95, explicit=True)
        elif "babylon.js" in text_low or "babylonjs" in text_low or "babylon" in text_low:
            add_state("renderer", "3d_engine", "Babylon.js", conf=0.95, explicit=True)

        # Frontend framework
        if "react" in text_low:
            add_state("framework", "frontend", "React", conf=0.92, explicit=True)
        elif "next.js" in text_low or "nextjs" in text_low:
            add_state("framework", "frontend", "Next.js", conf=0.92, explicit=True)
        elif "vue" in text_low:
            add_state("framework", "frontend", "Vue", conf=0.92, explicit=True)

        # Backend framework
        if "fastapi" in text_low:
            add_state("framework", "backend", "FastAPI", conf=0.95, explicit=True)
        elif "django" in text_low:
            add_state("framework", "backend", "Django", conf=0.95, explicit=True)
        elif "flask" in text_low:
            add_state("framework", "backend", "Flask", conf=0.95, explicit=True)

        # Database
        if "postgresql" in text_low or "postgres" in text_low:
            add_state("database", "primary_db", "PostgreSQL", conf=0.92, explicit=True)
        elif "redis" in text_low:
            add_state("database", "cache_broker", "Redis", conf=0.92, explicit=True)
        elif "sqlite" in text_low:
            add_state("database", "primary_db", "SQLite", conf=0.92, explicit=True)

        # Styling / Design System
        if "dark glass" in text_low or "glassmorphism" in text_low:
            add_state("styling", "theme", "Dark Glass Aesthetic", conf=0.88, explicit=True)
        elif "tailwind" in text_low:
            add_state("styling", "css_system", "Tailwind CSS", conf=0.90, explicit=True)

        return candidates

    # =========================================================================
    # DESIGN CONTEXT EXTRACTION
    # =========================================================================

    @classmethod
    def _extract_design_context(cls, lines: List[str], raw_text: str) -> List[str]:
        design_items: List[str] = []
        keywords = [
            "dark glass", "glassmorphism", "aesthetic", "minimal layout", "color palette",
            "large 3d visual", "typography", "dark mode", "light mode", "neon", "wireframe", "theme"
        ]
        text_low = raw_text.lower()
        for kw in keywords:
            if kw in text_low:
                # Find the sentence or phrase
                for line in lines:
                    if kw in line.lower() and len(line) < 140:
                        clean = re.sub(r'^[0-9\.\-\*\s#:]+', '', line).strip()
                        clean = sanitize_secrets(clean)
                        if clean and clean not in design_items:
                            design_items.append(clean)
                        break

        if not design_items and "glass" in text_low:
            design_items.append("Dark glass aesthetic with dynamic blur accents")

        return design_items[:6]

    # =========================================================================
    # PROJECT STATE EXTRACTION
    # =========================================================================

    @classmethod
    def _extract_project_state(cls, lines: List[str], raw_text: str) -> str:
        state_markers = re.findall(
            r'(?:current state|status:?|working state|we are at|progress:?)\s*[:\-]\s*([^\.\n]+)',
            raw_text,
            re.IGNORECASE
        )
        if state_markers:
            return sanitize_secrets(state_markers[0].strip().capitalize())

        # Check for phrases like "The GLB character has already been integrated"
        for line in lines:
            line_low = line.lower()
            if any(k in line_low for k in ["already integrated", "has been integrated", "implemented so far", "currently working"]):
                return sanitize_secrets(line.strip().capitalize())

        return "Active development underway. Structured Context OS entities identified and validated."

    # =========================================================================
    # VISUAL REFERENCE EXTRACTION & ASSOCIATION
    # =========================================================================

    @classmethod
    def _extract_visual_references(
        cls,
        lines: List[str],
        raw_text: str,
        project_id: Optional[str],
        current_user_id: Optional[str],
        db: Optional[Session],
        session_id: Optional[str],
        goals: List[ExtractedGoalCandidate],
        decisions: List[ExtractedDecisionCandidate],
        tasks: List[ExtractedTaskCandidate],
    ) -> List[ExtractedVisualReferenceCandidate]:
        candidates: List[ExtractedVisualReferenceCandidate] = []
        text_low = raw_text.lower()

        # Check if conversation mentions visual references
        has_visual_cue = any(
            any(re.search(pat, text_low) for pat in patterns)
            for patterns in cls.VISUAL_CUES.values()
        ) or any(w in text_low for w in ["screenshot", "image", "visual reference", ".png", ".jpg", ".webp"])

        if not has_visual_cue:
            return candidates

        # Determine visual role
        detected_role = "other"
        for role, patterns in cls.VISUAL_CUES.items():
            if any(re.search(pat, text_low) for pat in patterns):
                detected_role = role
                break

        # Grounded description construction (no vision model hallucination)
        description = None
        if detected_role == "character_reference":
            description = "User-provided character reference for project character implementation."
        elif detected_role == "ui_screenshot":
            description = "User screenshot demonstrating specific UI issue or bug state."
        elif detected_role == "design_reference":
            description = "User-provided design reference establishing aesthetic direction and visual layout."
        elif detected_role == "blender_render":
            description = "Render asset from Blender modeling pipeline."
        elif detected_role == "diagram":
            description = "Architectural or workflow reference diagram."
        else:
            description = "Visual reference asset captured from user interaction."

        # Extract potential visual tags
        visual_tags = []
        if "dark glass" in text_low or "glass" in text_low:
            visual_tags.append("dark-glass")
        if "portfolio" in text_low:
            visual_tags.append("portfolio")
        if "character" in text_low or "avatar" in text_low:
            visual_tags.append("character")
        if "bug" in text_low or "issue" in text_low:
            visual_tags.append("bug-report")
        if "3d" in text_low or "three.js" in text_low:
            visual_tags.append("3d-visual")

        # Associate with extracted goals, decisions, or tasks
        associated_goals = [g.title for g in goals[:2]]
        associated_decisions = [d.title for d in decisions if d.category in ["design_system", "renderer"]][:2]
        associated_tasks = [t.title for t in tasks if detected_role == "ui_screenshot" or "fix" in t.title.lower()][:2]

        # Match with existing database ContextImage if available
        matched_image_id = None
        original_filename = None

        if db and project_id and current_user_id:
            # Query images belonging to the project and user
            proj_images = (
                db.query(ContextImage)
                .filter(ContextImage.project_id == project_id, ContextImage.user_id == current_user_id)
                .order_by(ContextImage.created_at.desc())
                .all()
            )

            # Check if any image filename or ID is mentioned in transcript
            for img in proj_images:
                if (img.original_filename and img.original_filename.lower() in text_low) or (img.id in raw_text):
                    matched_image_id = img.id
                    original_filename = img.original_filename
                    break

            # If no explicit filename match, check for session image or most recent image
            if not matched_image_id and proj_images:
                if session_id:
                    session_img = next((img for img in proj_images if img.associated_session_id == session_id), None)
                    if session_img:
                        matched_image_id = session_img.id
                        original_filename = session_img.original_filename

                if not matched_image_id and len(proj_images) == 1:
                    matched_image_id = proj_images[0].id
                    original_filename = proj_images[0].original_filename

        candidates.append(
            ExtractedVisualReferenceCandidate(
                detected_image_id=matched_image_id,
                original_filename=original_filename,
                detected_role=detected_role,
                description=description,
                visual_tags=visual_tags,
                associated_goal_titles=associated_goals,
                associated_decision_titles=associated_decisions,
                associated_task_titles=associated_tasks,
                confidence=0.90 if matched_image_id else 0.80,
                explicit=True
            )
        )

        return candidates

    # =========================================================================
    # CONTRADICTION DETECTION
    # =========================================================================

    @classmethod
    def _detect_contradictions(
        cls,
        candidate_decisions: List[ExtractedDecisionCandidate],
        candidate_goals: List[ExtractedGoalCandidate],
        project_id: Optional[str],
        db: Optional[Session],
    ) -> List[ContradictionItem]:
        contradictions: List[ContradictionItem] = []

        # 1. Existing DB decisions vs candidate decisions
        existing_decisions: List[ContextDecision] = []
        if db and project_id:
            existing_decisions = (
                db.query(ContextDecision)
                .filter(ContextDecision.project_id == project_id, ContextDecision.status == "accepted")
                .all()
            )

        # Build list of statements to test
        context_data = {
            "objective": "",
            "requirements": [g.title for g in candidate_goals if g.category == "requirement"],
            "constraints": [g.title for g in candidate_goals if g.category == "constraint"],
            "decisions": [d.title for d in candidate_decisions] + [ed.title for ed in existing_decisions],
            "current_state": ""
        }

        raw_contradictions = ContradictionDetector.analyze(context_data)
        for rc in raw_contradictions:
            contradictions.append(
                ContradictionItem(
                    severity=rc["severity"],
                    topic=rc["topic"],
                    earlier_statement=rc["earlier_statement"],
                    later_statement=rc["later_statement"],
                    explanation=rc["explanation"]
                )
            )

        # 2. Check Three.js vs Babylon.js pairwise (specific rendering pair)
        all_decision_texts = [d.title.lower() for d in candidate_decisions] + [ed.title.lower() for ed in existing_decisions]
        has_three = any("three.js" in t or "threejs" in t for t in all_decision_texts)
        has_babylon = any("babylon" in t for t in all_decision_texts)
        if has_three and has_babylon:
            contradictions.append(
                ContradictionItem(
                    severity="warning",
                    topic="3D Rendering Engine",
                    earlier_statement="Decision: Three.js",
                    later_statement="Decision: Babylon.js",
                    explanation="Conflicting 3D Rendering Engine choices detected (Three.js vs Babylon.js). Confirm the active architectural choice."
                )
            )

        return contradictions

    # =========================================================================
    # PERSISTENCE & ASSOCIATION
    # =========================================================================

    @classmethod
    def persist_extracted_context(
        cls,
        extracted: StructuredExtractionResult,
        project: Project,
        user: User,
        db: Session,
        session_id: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Safely persist structured extraction candidates into the database.
        Applies deduplication, decision superseding, tenant isolation, and image associations.
        """
        persisted = {
            "goals": 0,
            "decisions": 0,
            "tasks": 0,
            "technical_states": 0,
            "visual_associations": 0,
        }

        # 1. Persist Goals with deduplication
        existing_goals = db.query(ContextGoal).filter(ContextGoal.project_id == project.id).all()
        existing_goal_norms = {re.sub(r'[^a-z0-9]', '', g.title.lower()): g for g in existing_goals}

        goal_map = {}  # title -> model
        for gc in extracted.goals:
            norm = re.sub(r'[^a-z0-9]', '', gc.title.lower())
            if norm in existing_goal_norms:
                goal_map[gc.title] = existing_goal_norms[norm]
                continue

            goal = ContextGoal(
                project_id=project.id,
                user_id=user.id,
                title=gc.title[:255],
                description=gc.description,
                category=gc.category,
                priority=gc.priority,
                status="active",
                source_session_id=session_id
            )
            db.add(goal)
            db.flush()
            existing_goal_norms[norm] = goal
            goal_map[gc.title] = goal
            persisted["goals"] += 1

        # 2. Persist Decisions with superseding and deduplication
        existing_decisions = db.query(ContextDecision).filter(ContextDecision.project_id == project.id).all()
        existing_dec_norms = {re.sub(r'[^a-z0-9]', '', d.title.lower()): d for d in existing_decisions}

        decision_map = {}  # title -> model
        for dc in extracted.decisions:
            norm = re.sub(r'[^a-z0-9]', '', dc.title.lower())
            if norm in existing_dec_norms:
                decision_map[dc.title] = existing_dec_norms[norm]
                continue

            # Check if this decision supersedes an existing decision in the same category
            superseded_id = None
            if dc.status == "accepted":
                for ed in existing_decisions:
                    if ed.status == "accepted" and ed.category == dc.category and ed.title.lower() != dc.title.lower():
                        # If contradiction or replacement keyword like 'switched to'
                        if any(k in dc.title.lower() for k in ["switch", "replace", "instead of", "migrat"]) or any(
                            group["category"] == ed.category for group in MUTUALLY_EXCLUSIVE_GROUPS
                        ):
                            ed.status = "superseded"
                            superseded_id = ed.id
                            break

            decision = ContextDecision(
                project_id=project.id,
                user_id=user.id,
                title=dc.title[:255],
                description=dc.description,
                rationale=dc.rationale,
                category=dc.category,
                status=dc.status,
                source_session_id=session_id,
                superseded_by_id=superseded_id
            )
            db.add(decision)
            db.flush()

            if superseded_id:
                # Update superseded decision's superseded_by_id to point to the new decision
                sup_dec = db.query(ContextDecision).filter(ContextDecision.id == superseded_id).first()
                if sup_dec:
                    sup_dec.superseded_by_id = decision.id

            existing_dec_norms[norm] = decision
            decision_map[dc.title] = decision
            persisted["decisions"] += 1

        # Also persist explicit design context as a design_system decision if not already present
        if extracted.design_context:
            for dc_text in extracted.design_context:
                norm = re.sub(r'[^a-z0-9]', '', dc_text.lower())
                if norm not in existing_dec_norms:
                    design_dec = ContextDecision(
                        project_id=project.id,
                        user_id=user.id,
                        title=f"Design System: {dc_text[:230]}",
                        description=f"Extracted design directive: {dc_text}",
                        category="design_system",
                        status="accepted",
                        source_session_id=session_id
                    )
                    db.add(design_dec)
                    db.flush()
                    existing_dec_norms[norm] = design_dec
                    persisted["decisions"] += 1

        # 3. Persist Tasks with deduplication
        existing_tasks = db.query(ContextTask).filter(ContextTask.project_id == project.id).all()
        existing_task_norms = {re.sub(r'[^a-z0-9]', '', t.title.lower()): t for t in existing_tasks}

        task_map = {}  # title -> model
        for tc in extracted.tasks:
            norm = re.sub(r'[^a-z0-9]', '', tc.title.lower())
            if norm in existing_task_norms:
                task_map[tc.title] = existing_task_norms[norm]
                continue

            task = ContextTask(
                project_id=project.id,
                user_id=user.id,
                title=tc.title[:255],
                description=tc.description,
                status=tc.status,
                priority=tc.priority,
                source_session_id=session_id
            )
            db.add(task)
            db.flush()
            existing_task_norms[norm] = task
            task_map[tc.title] = task
            persisted["tasks"] += 1

        # 4. Persist Technical States with upsert logic on (project_id, category, key)
        for sc in extracted.technical_states:
            existing_state = (
                db.query(ContextTechnicalState)
                .filter(
                    ContextTechnicalState.project_id == project.id,
                    ContextTechnicalState.category == sc.category,
                    ContextTechnicalState.key == sc.key,
                )
                .first()
            )
            if existing_state:
                if existing_state.value != sc.value:
                    existing_state.value = sc.value
                    existing_state.updated_at = utc_now()
                    persisted["technical_states"] += 1
            else:
                new_state = ContextTechnicalState(
                    project_id=project.id,
                    user_id=user.id,
                    category=sc.category,
                    key=sc.key,
                    value=sc.value,
                    source_session_id=session_id
                )
                db.add(new_state)
                persisted["technical_states"] += 1

        # 5. Link Visual Assets (ContextImage associations)
        for vref in extracted.visual_references:
            if not vref.detected_image_id:
                continue

            # Strict Tenant Isolation Check: verify target image belongs to project & user
            img = db.query(ContextImage).filter(ContextImage.id == vref.detected_image_id).first()
            if not img or img.project_id != project.id or img.user_id != user.id:
                continue  # Reject foreign or cross-tenant image association

            updated_image = False

            # Update image_type if useful
            if vref.detected_role != "other" and img.image_type in ["other", "ai_conversation_capture"]:
                img.image_type = vref.detected_role
                updated_image = True

            # Update description if better grounded
            if vref.description and (not img.description or "uploaded" in img.description.lower()):
                img.description = vref.description
                updated_image = True

            # Associate Context Goals & Tasks in associated_context_ids
            cur_ctx_ids = img.get_list("associated_context_ids")
            for g_title in vref.associated_goal_titles:
                if g_title in goal_map:
                    gid = goal_map[g_title].id
                    if gid not in cur_ctx_ids:
                        cur_ctx_ids.append(gid)
                        updated_image = True

            for t_title in vref.associated_task_titles:
                if t_title in task_map:
                    tid = task_map[t_title].id
                    if tid not in cur_ctx_ids:
                        cur_ctx_ids.append(tid)
                        updated_image = True
            img.set_list("associated_context_ids", cur_ctx_ids)

            # Associate Decisions in associated_decision_ids
            cur_dec_ids = img.get_list("associated_decision_ids")
            for d_title in vref.associated_decision_titles:
                if d_title in decision_map:
                    did = decision_map[d_title].id
                    if did not in cur_dec_ids:
                        cur_dec_ids.append(did)
                        updated_image = True
            img.set_list("associated_decision_ids", cur_dec_ids)

            # Associate Session ID
            if session_id and not img.associated_session_id:
                img.associated_session_id = session_id
                updated_image = True

            # Update visual tags
            if vref.visual_tags:
                cur_tags = img.get_list("visual_tags")
                for tag in vref.visual_tags:
                    if tag not in cur_tags:
                        cur_tags.append(tag)
                        updated_image = True
                img.set_list("visual_tags", cur_tags)

            if updated_image:
                img.updated_at = utc_now()
                persisted["visual_associations"] += 1

        db.commit()
        return persisted
