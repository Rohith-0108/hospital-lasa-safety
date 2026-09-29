"""
baseline.py

Models the CURRENT-STATE process at the hospital pharmacy: a plain
name-lookup pick-list of the kind found in many legacy dispensing/EHR
systems.

Behaviour (intentionally simple, matching real legacy UX):
  - Matches medicines whose name starts with or contains the typed text.
  - Sorts results alphabetically (not by clinical relevance or risk).
  - Auto-highlights the first result as the presumed selection.
  - Has NO concept of confidence, risk, tall-man lettering, packaging
    similarity, barcode confirmation or mandatory double-check.

This is the comparator the proposed safety-aware engine is measured against.
"""
from src.data_loader import load_medicines


class BaselineEngine:
    def __init__(self, medicines=None):
        self.medicines = medicines if medicines is not None else load_medicines()

    def search(self, query: str) -> list[dict]:
        q = query.strip().lower()
        if not q:
            return []
        starts = [m for m in self.medicines if m["name"].lower().startswith(q)]
        contains = [m for m in self.medicines
                    if q in m["name"].lower() and m not in starts]
        results = sorted(starts, key=lambda m: m["name"]) + \
            sorted(contains, key=lambda m: m["name"])
        return results

    def pick(self, query: str) -> dict | None:
        """Simulates the baseline UX: first alphabetical match is auto-selected."""
        results = self.search(query)
        return results[0] if results else None
