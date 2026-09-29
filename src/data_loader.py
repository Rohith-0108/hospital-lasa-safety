"""data_loader.py - loads data/medicines.csv and data/lasa_pairs.csv into memory."""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MED_CSV = os.path.join(ROOT, "data", "medicines.csv")
PAIRS_CSV = os.path.join(ROOT, "data", "lasa_pairs.csv")


def load_medicines(path: str = MED_CSV) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_lasa_pairs(path: str = PAIRS_CSV) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def known_pair_lookup(pairs: list[dict]) -> dict:
    """Returns {id: {other_id: pair_record}} for O(1) known-pair checks."""
    lookup: dict = {}
    for p in pairs:
        a, b = p["id_a"], p["id_b"]
        lookup.setdefault(a, {})[b] = p
        lookup.setdefault(b, {})[a] = p
    return lookup
