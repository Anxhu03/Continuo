"""
CONTINUO — Context Quality Scorer
Calculates authentic dynamic quality scores (0–100%) and generates diagnostic recommendations.
"""

from typing import Dict, Any, List
from backend.services.contradiction import ContradictionDetector

class QualityScorer:
    """
    Evaluates ContextPackage completeness, structural clarity, constraint density,
    and consistency risk to yield an authentic mathematical score.
    """

    @classmethod
    def evaluate(cls, context_data: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Completeness Score (Max: 30)
        completeness = 0.0
        obj = context_data.get("objective") or ""
        if len(obj) > 15:
            completeness += 8.0
        elif len(obj) > 5:
            completeness += 4.0
        
        req_count = len(context_data.get("requirements", []))
        if req_count >= 3:
            completeness += 8.0
        elif req_count >= 1:
            completeness += 4.0 + min(3.0, req_count * 1.5)

        const_count = len(context_data.get("constraints", []))
        if const_count >= 2:
            completeness += 6.0
        elif const_count >= 1:
            completeness += 4.0

        dec_count = len(context_data.get("decisions", []))
        if dec_count >= 2:
            completeness += 5.0
        elif dec_count >= 1:
            completeness += 3.5

        if context_data.get("current_state") and len(context_data["current_state"]) > 5:
            completeness += 3.0

        completeness = min(30.0, completeness)

        # 2. Structural Clarity & Depth (Max: 25)
        clarity = 0.0
        files_count = len(context_data.get("files_context", []))
        if files_count >= 2:
            clarity += 8.0
        elif files_count == 1:
            clarity += 5.0
        else:
            if len(context_data.get("instructions", [])) > 0:
                clarity += 4.0

        dep_count = len(context_data.get("dependencies", []))
        if dep_count >= 2:
            clarity += 6.0
        elif dep_count == 1:
            clarity += 4.0

        done_count = len(context_data.get("completed_work", []))
        if done_count >= 2:
            clarity += 6.0
        elif done_count == 1:
            clarity += 4.0

        inst_count = len(context_data.get("instructions", []))
        if inst_count >= 2:
            clarity += 5.0
        elif inst_count == 1 or dec_count >= 2:
            clarity += 3.0

        clarity = min(25.0, clarity)

        # 3. Actionability & Operational Readiness (Max: 25)
        actionability = 0.0
        next_count = len(context_data.get("next_steps", []))
        if next_count >= 2:
            actionability += 10.0
        elif next_count == 1:
            actionability += 6.5

        pending_count = len(context_data.get("pending_work", []))
        if pending_count >= 2:
            actionability += 8.0
        elif pending_count == 1:
            actionability += 5.5

        failed_count = len(context_data.get("failed_attempts", []))
        prob_count = len(context_data.get("open_problems", []))
        if (failed_count + prob_count) >= 1:
            actionability += 7.0
        elif next_count >= 1 and pending_count >= 1:
            actionability += 4.5

        actionability = min(25.0, actionability)

        # 4. Consistency & Contradiction Risk (Max: 20)
        contradictions = ContradictionDetector.analyze(context_data)
        consistency = 20.0
        for c in contradictions:
            if c["severity"] == "critical":
                consistency -= 10.0
            else:
                consistency -= 5.0
        consistency = max(0.0, consistency)

        total_score = round(completeness + clarity + actionability + consistency, 1)
        total_score = max(5.0, min(100.0, total_score))

        # Recommendations
        recommendations = []
        if req_count < 3:
            recommendations.append("Specify at least 3 explicit functional requirements.")
        if const_count < 2:
            recommendations.append("Document non-negotiable architectural constraints to prevent AI drift.")
        if files_count == 0:
            recommendations.append("Tag primary file paths or code locations to give direct grounding.")
        if failed_count == 0:
            recommendations.append("Note rejected approaches or dead ends so downstream models don't repeat them.")
        if contradictions:
            recommendations.append(f"Resolve {len(contradictions)} detected architectural contradiction(s).")
        if not recommendations:
            recommendations.append("Context package has high operational fidelity and is ready for model transit.")

        return {
            "overall_score": total_score,
            "breakdown": {
                "completeness": round(completeness, 1),
                "clarity_and_depth": round(clarity, 1),
                "actionability": round(actionability, 1),
                "consistency": round(consistency, 1)
            },
            "contradictions": contradictions,
            "recommendations": recommendations
        }
