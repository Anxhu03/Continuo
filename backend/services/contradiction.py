"""
CONTINUO — Contradiction Detection Service
Analyzes project requirements and architectural decisions for conflicting or mutually exclusive paths.
"""

import re
from typing import List, Dict, Any

# Known mutually exclusive technology / architecture pairs
MUTUALLY_EXCLUSIVE_GROUPS = [
    {
        "category": "Primary Database",
        "options": ["postgresql", "postgres", "mongodb", "mysql", "dynamodb", "neo4j", "couchdb"]
    },
    {
        "category": "Backend Framework",
        "options": ["fastapi", "flask", "django", "express", "nestjs", "rails", "spring boot"]
    },
    {
        "category": "API Protocol",
        "options": ["rest api", "graphql", "grpc", "trpc", "soap"]
    },
    {
        "category": "CSS Architecture",
        "options": ["vanilla css", "tailwind css", "styled-components", "sass", "css modules"]
    },
    {
        "category": "Language Runtime",
        "options": ["typescript", "javascript", "python", "golang", "rust", "ruby"]
    },
    {
        "category": "Auth Provider",
        "options": ["supabase auth", "auth0", "firebase auth", "clerk", "nextauth", "custom jwt"]
    }
]

class ContradictionDetector:
    """
    Scans ContextPackage items and transcripts to flag architectural and constraint contradictions.
    """

    @classmethod
    def analyze(cls, context_data: Dict[str, Any]) -> List[Dict[str, str]]:
        contradictions = []

        all_statements = []
        all_statements.extend([("Objective", context_data.get("objective", ""))])
        all_statements.extend([("Requirement", r) for r in context_data.get("requirements", [])])
        all_statements.extend([("Constraint", c) for c in context_data.get("constraints", [])])
        all_statements.extend([("Decision", d) for d in context_data.get("decisions", [])])
        all_statements.extend([("Current State", context_data.get("current_state", ""))])

        # 1. Mutually Exclusive Technology Detection
        for group in MUTUALLY_EXCLUSIVE_GROUPS:
            category = group["category"]
            detected = []
            for src_type, text in all_statements:
                text_lower = text.lower()
                for opt in group["options"]:
                    if re.search(r'\b' + re.escape(opt) + r'\b', text_lower):
                        detected.append((opt, src_type, text))

            # Deduplicate by technology option name
            unique_detected = {}
            for opt, src_type, text in detected:
                if opt not in unique_detected:
                    unique_detected[opt] = (src_type, text)

            if len(unique_detected) > 1:
                keys = list(unique_detected.keys())
                opt_a, opt_b = keys[0], keys[1]
                src_a, text_a = unique_detected[opt_a]
                src_b, text_b = unique_detected[opt_b]

                contradictions.append({
                    "severity": "warning",
                    "topic": category,
                    "earlier_statement": f"[{src_a}] {text_a}",
                    "later_statement": f"[{src_b}] {text_b}",
                    "explanation": f"Conflicting {category} choices detected ({opt_a.title()} vs {opt_b.title()}). Confirm the active architectural choice."
                })

        # 2. Negation / Polar Contradiction Detection
        # Check if something in requirements conflicts directly with constraints
        reqs = context_data.get("requirements", [])
        constraints = context_data.get("constraints", [])
        COMMON_VERBS = {"store", "use", "make", "allow", "expose", "have", "run", "be", "with", "from", "any", "the", "a", "an", "under", "in"}

        for r in reqs:
            r_low = r.lower()
            for c in constraints:
                c_low = c.lower()
                # Check for "Do not use X", "never use X", "avoid X", "strictly prohibit X"
                prohibitions = re.findall(r'(?:do not use|never use|avoid using|avoid|do not adopt|strictly prohibit|cannot use|no)\s+([a-z0-9_\-]+)', c_low)
                for term in prohibitions:
                    term = term.strip()
                    if len(term) > 3 and term not in COMMON_VERBS and re.search(r'\b' + re.escape(term) + r'\b', r_low):
                        contradictions.append({
                            "severity": "critical",
                            "topic": f"Forbidden Element: {term.title()}",
                            "earlier_statement": f"[Requirement] {r}",
                            "later_statement": f"[Constraint] {c}",
                            "explanation": f"Constraint strictly prohibits '{term}', but a requirement demands it."
                        })

        return contradictions
