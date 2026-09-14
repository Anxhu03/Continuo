"""
CONTINUO — Version Diff Service
Computes structured diffs (Added, Modified, Removed) between Context Package revisions.
"""

from typing import Dict, Any, List

class VersionDiffEngine:
    """
    Compares two Context Packages and produces semantic differences across lists and state descriptions.
    """

    @classmethod
    def compute_diff(
        cls,
        v_old: Dict[str, Any],
        v_new: Dict[str, Any],
        from_ver: str,
        to_ver: str,
        project_id: str
    ) -> Dict[str, Any]:
        added: Dict[str, List[str]] = {}
        removed: Dict[str, List[str]] = {}
        modified: Dict[str, Dict[str, str]] = {}

        # 1. Compare Scalar Fields
        scalar_fields = ["objective", "current_state"]
        for field in scalar_fields:
            old_val = v_old.get(field, "").strip()
            new_val = v_new.get(field, "").strip()
            if old_val != new_val:
                modified[field] = {
                    "previous": old_val,
                    "current": new_val
                }

        # 2. Compare List Fields
        list_fields = [
            "requirements", "constraints", "instructions", "decisions",
            "completed_work", "pending_work", "open_problems", "failed_attempts",
            "files_context", "design_decisions", "dependencies", "next_steps"
        ]

        for field in list_fields:
            old_list = set(v_old.get(field, []))
            new_list = set(v_new.get(field, []))

            additions = list(new_list - old_list)
            removals = list(old_list - new_list)

            if additions:
                added[field] = additions
            if removals:
                removed[field] = removals

        # 3. Generate Summary Text
        total_adds = sum(len(items) for items in added.values())
        total_rems = sum(len(items) for items in removed.values())
        total_mods = len(modified)

        summary_parts = []
        if total_adds:
            summary_parts.append(f"{total_adds} items added")
        if total_mods:
            summary_parts.append(f"{total_mods} fields updated")
        if total_rems:
            summary_parts.append(f"{total_rems} items retired")

        summary = ", ".join(summary_parts) if summary_parts else "No meaningful changes detected."

        return {
            "project_id": project_id,
            "from_version": from_ver,
            "to_version": to_ver,
            "added": added,
            "modified": modified,
            "removed": removed,
            "summary": summary
        }
