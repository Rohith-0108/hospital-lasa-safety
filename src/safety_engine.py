"""
safety_engine.py

The PROPOSED system. For every candidate medicine returned for a typed or
spoken query, this engine attaches an explicit, visible risk assessment
instead of silently auto-selecting the "best" match the way the baseline
does.

Design principles (see docs/architecture.md for the full rationale):
  1. Uncertainty is always shown, never hidden. Every result carries a
     confidence score and, where relevant, the identity of the medicine it
     could be confused with and *why*.
  2. Risk drives friction. Low-risk picks are fast; Critical/High-risk picks
     require a second, independent human check and a barcode/shelf
     confirmation before dispensing is allowed to proceed.
  3. Ties are never auto-resolved. If two candidates are within
     TIE_MARGIN of each other, the system refuses to presume which one the
     user meant and forces explicit disambiguation.
  4. Known LASA pairs (data/lasa_pairs.csv, curated from institutional
     safety bulletins) are treated as a floor, not a ceiling: the engine
     also flags *newly detected* similar pairs it wasn't told about, using
     the same similarity function that would generalise to future stock.
"""
from src.data_loader import load_medicines, load_lasa_pairs, known_pair_lookup
from src.similarity import combined_similarity

SIMILARITY_ALERT_THRESHOLD = 0.55   # below this, names are considered unrelated
TIE_MARGIN = 0.05                   # candidates within this score are an ambiguous tie

RISK_ORDER = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}


def _risk_from_similarity(score: float) -> str:
    if score >= 0.85:
        return "Critical"
    if score >= 0.70:
        return "High"
    if score >= SIMILARITY_ALERT_THRESHOLD:
        return "Medium"
    return "Low"


class SafetyEngine:
    def __init__(self, medicines=None, pairs=None):
        self.medicines = medicines if medicines is not None else load_medicines()
        self.pairs = pairs if pairs is not None else load_lasa_pairs()
        self.pair_lookup = known_pair_lookup(self.pairs)
        self.by_id = {m["id"]: m for m in self.medicines}

    # ---------- searching ----------

    def search(self, query: str) -> list[dict]:
        q = query.strip()
        if not q:
            return []
        scored = []
        for m in self.medicines:
            score = max(
                combined_similarity(q, m["name"]),
                combined_similarity(q, m["generic"]),
            )
            if q.lower() in m["name"].lower() or m["name"].lower().startswith(q.lower()):
                score = max(score, 0.92)  # substring/prefix matches rank near the top
            if score > 0.15:
                scored.append((score, m))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [dict(m, match_confidence=round(score, 3)) for score, m in scored]

    # ---------- risk assessment ----------

    def find_confusable_neighbors(self, candidate: dict) -> list[dict]:
        """All other medicines that are visually/phonetically/orthographically
        close to `candidate`, whether or not they are in the curated pair list."""
        neighbors = []
        known_others = self.pair_lookup.get(candidate["id"], {})
        for other in self.medicines:
            if other["id"] == candidate["id"]:
                continue
            sim = max(
                combined_similarity(candidate["name"], other["name"]),
                combined_similarity(candidate["generic"], other["generic"]),
            )
            known = known_others.get(other["id"])
            if known or sim >= SIMILARITY_ALERT_THRESHOLD:
                tier = known["reference_risk_tier"] if known else _risk_from_similarity(sim)
                neighbors.append({
                    "id": other["id"],
                    "name": other["name"],
                    "similarity": round(sim, 3),
                    "risk_tier": tier,
                    "confusion_type": known["confusion_type"] if known else "detected-similarity",
                    "harm_if_confused": other["harm_if_confused"],
                })
        neighbors.sort(key=lambda n: (RISK_ORDER[n["risk_tier"]], n["similarity"]), reverse=True)
        return neighbors

    def assess(self, query: str, candidate_id: str) -> dict:
        results = self.search(query)
        candidate = self.by_id[candidate_id]
        candidate_result = next((r for r in results if r["id"] == candidate_id), None)
        confidence = candidate_result["match_confidence"] if candidate_result else 0.5

        neighbors = self.find_confusable_neighbors(candidate)
        top_neighbor = neighbors[0] if neighbors else None
        risk_level = top_neighbor["risk_tier"] if top_neighbor else "Low"

        ambiguous_tie = False
        if len(results) >= 2:
            ambiguous_tie = (results[0]["match_confidence"] - results[1]["match_confidence"]) < TIE_MARGIN \
                and results[0]["id"] != results[1]["id"]

        requires_second_check = risk_level in ("Medium", "High", "Critical") or ambiguous_tie
        requires_barcode = risk_level in ("High", "Critical")

        return {
            "query": query,
            "candidate": candidate,
            "confidence": confidence,
            "risk_level": risk_level,
            "ambiguous_tie": ambiguous_tie,
            "tie_candidates": [r["id"] for r in results[:3]] if ambiguous_tie else [],
            "confusable_with": neighbors,
            "harm_if_wrong": candidate["harm_if_confused"],
            "requires_second_check": requires_second_check,
            "requires_barcode_scan": requires_barcode,
            "tallman": candidate["tallman"],
        }

    # ---------- physical confirmation checks ----------

    def check_barcode(self, candidate_id: str, scanned_id: str) -> bool:
        """In the real system the barcode encodes a stock unit ID. Here the
        medicine `id` stands in for that code."""
        return candidate_id == scanned_id

    def check_shelf(self, candidate_id: str, scanned_shelf: str) -> bool:
        return self.by_id[candidate_id]["shelf_location"] == scanned_shelf
