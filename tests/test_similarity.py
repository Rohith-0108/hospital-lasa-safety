import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.similarity import levenshtein_distance, orthographic_similarity, soundex, combined_similarity


def test_levenshtein_identical():
    assert levenshtein_distance("hydralazine", "hydralazine") == 0


def test_levenshtein_basic():
    assert levenshtein_distance("cat", "bat") == 1


def test_orthographic_similarity_range():
    s = orthographic_similarity("hydralazine", "hydroxyzine")
    assert 0.0 < s < 1.0


def test_soundex_known_example():
    assert soundex("Robert") == soundex("Rupert")


def test_combined_similarity_orthographic_pair_scores_higher_than_unrelated():
    # Hydralazine/Hydroxyzine share a long prefix - pure orthographic
    # similarity should clearly separate them from an unrelated pair.
    lasa = combined_similarity("Hydralazine", "Hydroxyzine")
    unrelated = combined_similarity("Paracetamol", "Vincristine")
    assert lasa > unrelated
    assert lasa > 0.5


def test_combined_similarity_alone_does_not_catch_every_known_pair():
    # Documents a known limitation: some institutionally-recognised LASA
    # pairs (e.g. Losartan/Lorazepam) are confusable in practice (similar
    # handwriting/shelf position) but score lower on pure edit-distance +
    # Soundex than same-prefix pairs. This is exactly why safety_engine.py
    # also consults a curated pair list (data/lasa_pairs.csv) rather than
    # relying on the similarity function alone - see docs/error_analysis.md.
    s = combined_similarity("Losartan", "Lorazepam")
    assert s < 0.5
