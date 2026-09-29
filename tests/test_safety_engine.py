import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.safety_engine import SafetyEngine
from src.baseline import BaselineEngine

engine = SafetyEngine()
baseline = BaselineEngine()


def test_known_lasa_pair_flagged_high_risk():
    a = engine.assess("Hydromorphone", "M09")
    assert a["risk_level"] in ("High", "Critical")
    assert a["requires_second_check"] is True
    assert a["requires_barcode_scan"] is True
    assert any(n["id"] == "M10" for n in a["confusable_with"])


def test_curated_pair_flagged_even_when_raw_similarity_score_is_low():
    # Losartan/Lorazepam score low on pure Levenshtein+Soundex similarity
    # (see tests/test_similarity.py) but are a well-known institutional LASA
    # pair. The engine must still flag it because it consults the curated
    # pair list, not similarity score alone.
    a = engine.assess("Losartan", "M11")
    assert a["risk_level"] == "High"
    assert any(n["id"] == "M12" for n in a["confusable_with"])


def test_control_item_is_low_risk_no_friction():
    a = engine.assess("Paracetamol", "M17")
    assert a["risk_level"] == "Low"
    assert a["requires_second_check"] is False
    assert a["requires_barcode_scan"] is False


# ---------------------------------------------------------------------------
# EDGE / FAILURE CASE 1: Ambiguous tie - two near-identical scoring candidates
# must NOT be auto-resolved; the system must force manual disambiguation.
# ---------------------------------------------------------------------------
def test_edge_case_ambiguous_tie_forces_disambiguation():
    a = engine.assess("Vin", "M03")  # short prefix common to both vinblastine/vincristine
    assert a["ambiguous_tie"] is True
    assert len(a["tie_candidates"]) >= 2


# ---------------------------------------------------------------------------
# EDGE / FAILURE CASE 2: Barcode scan mismatch must block dispensing even if
# the on-screen name looked correct to the human.
# ---------------------------------------------------------------------------
def test_edge_case_barcode_mismatch_blocks():
    # Technician believes they picked morphine (M10) but scans the
    # hydromorphone (M09) vial pulled from an adjacent bin.
    assert engine.check_barcode("M10", "M09") is False
    assert engine.check_barcode("M10", "M10") is True


# ---------------------------------------------------------------------------
# EDGE / FAILURE CASE 3: Shelf location mismatch - item was restocked in the
# wrong bin; system must not silently trust the expected location.
# ---------------------------------------------------------------------------
def test_edge_case_shelf_mismatch_detected():
    # Insulin Lispro's correct shelf is W-05-A; simulate scanning from the
    # neighbouring Glargine bin (W-05-B) instead.
    assert engine.check_shelf("M07", "W-05-B") is False
    assert engine.check_shelf("M07", "W-05-A") is True


# ---------------------------------------------------------------------------
# EDGE / FAILURE CASE 4: Baseline has none of these protections - included so
# the contrast is explicit and testable, not just asserted in prose.
# ---------------------------------------------------------------------------
def test_edge_case_baseline_has_no_risk_awareness():
    pick = baseline.pick("Vin")
    # Baseline returns *a* result with no risk flag, no confidence, no
    # mechanism to detect that "Vin" is dangerously ambiguous.
    assert pick is not None
    assert "risk_level" not in pick
    assert "match_confidence" not in pick
