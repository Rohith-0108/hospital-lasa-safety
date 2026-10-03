
"""
simulate_dispensing.py

The measurable experiment: a controlled, reproducible dispensing test that
compares the CURRENT-STATE baseline pick-list against the PROPOSED
safety-aware engine on the same set of simulated prescription inputs.

Method
------
For every known LASA pair (data/lasa_pairs.csv) we generate simulated
"selection events": a pharmacy technician/nurse types or transcribes a
verbal/handwritten order for medicine A, but the input is corrupted in a
way that is realistic for that confusion type:
  - the typed text is shifted toward the confusable
    partner's name (simulating a controlled transcription / typing error)
  - this same input-corruption approach is used for both sound-alike and
    look-alike pairs; physical packaging/shelf verification is represented
    through the proposed safety checks rather than a separate visual simulation.

We also run a block of "control" trials on non-LASA medicines to measure
false positives / added friction the proposed system introduces on safe,
unambiguous picks.

Baseline outcome:  first-ranked baseline.pick() result is taken as the
                    item that would physically be dispensed. If that item is
                    the WRONG (confusable) medicine, it's a selection error.

Proposed outcome:   the same corrupted input goes through SafetyEngine. If
                    the top candidate requires a second-check, that check is
                    simulated using SECOND_CHECK_CATCH_RATE.

                    For High/Critical candidates, the prototype additionally
                    models barcode verification. A barcode mismatch catches
                    the wrong candidate.

                    SECOND_CHECK_CATCH_RATE is a documented modelling
                    ASSUMPTION - see docs/stakeholder_assumptions.md -
                    not an empirical clinical finding.

This file has zero external dependencies and is fully deterministic given a
fixed random seed, so results are reproducible.
"""

import json
import os
import random

from src.data_loader import load_medicines, load_lasa_pairs
from src.baseline import BaselineEngine
from src.safety_engine import SafetyEngine


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(ROOT, "results")

SEED = 42
TRIALS_PER_PAIR = 100
CONTROL_TRIALS_PER_ITEM = 40

# ASSUMPTION:
# An independent second check catches 88% of errors that reach it.
# This is a modelling assumption, not empirical clinical evidence.
SECOND_CHECK_CATCH_RATE = 0.88

# Stakeholder-set prototype target.
TARGET_REDUCTION = 0.90


def corrupt_name(
    correct_name: str,
    confusable_name: str,
    rng: random.Random,
) -> str:
    """
    Simulate a realistic noisy input.

    The input can represent:
      - a full wrong-name swap
      - a partial prefix
      - a near-miss character substitution
    """

    a, b = correct_name, confusable_name

    style = rng.random()

    if style < 0.35:
        # Full swap: wrong name entered outright.
        return b

    elif style < 0.70:
        # Partial input: first several characters.
        n = rng.randint(
            3,
            min(len(a), len(b), 7),
        )
        return a[:n]

    else:
        # Near miss: one character changed toward the
        # confusable medicine name.
        if len(a) == 0:
            return a

        idx = rng.randrange(len(a))

        repl = (
            b[idx]
            if idx < len(b)
            else a[idx]
        )

        return (
            a[:idx]
            + repl
            + a[idx + 1:]
        )


def run_experiment(seed: int = SEED):
    """
    Run the reproducible before/after experiment.
    """

    rng = random.Random(seed)

    medicines = load_medicines()
    pairs = load_lasa_pairs()

    by_id = {
        m["id"]: m
        for m in medicines
    }

    baseline = BaselineEngine(medicines)
    safety = SafetyEngine(medicines, pairs)

    # M17 and M18 are the non-LASA control medicines.
    control_ids = [
        m["id"]
        for m in medicines
        if m["id"] in ("M17", "M18")
    ]

    trial_log = []
    pair_breakdown = {}

    def log_pair_stats(pair_key):
        pair_breakdown.setdefault(
            pair_key,
            {
                "trials": 0,
                "baseline_errors": 0,
                "proposed_errors": 0,
            },
        )

    # ---------------------------------------------------------
    # LASA-pair trials
    # ---------------------------------------------------------

    for p in pairs:

        a_id = p["id_a"]
        b_id = p["id_b"]

        a = by_id[a_id]
        b = by_id[b_id]

        pair_key = (
            f"{a['name']} / {b['name']}"
        )

        log_pair_stats(pair_key)

        for i in range(TRIALS_PER_PAIR):

            # Alternate intended medicine.
            intended, other = (
                (a, b)
                if i % 2 == 0
                else (b, a)
            )

            typed = corrupt_name(
                intended["name"],
                other["name"],
                rng,
            )

            # -------------------------------------------------
            # Baseline outcome
            # -------------------------------------------------

            b_pick = baseline.pick(typed)

            baseline_error = (
                bool(b_pick)
                and b_pick["id"] != intended["id"]
                and b_pick["id"] in (a_id, b_id)
            )

            # If baseline found nothing, treat it as a near miss,
            # not an automatic selection error.
            if not b_pick:
                baseline_error = False

            # -------------------------------------------------
            # Proposed outcome
            # -------------------------------------------------

            results = safety.search(typed)

            top = (
                results[0]
                if results
                else None
            )

            proposed_error = False
            flagged = False
            barcode_required = False
            barcode_passed = None
            second_check_caught = None

            if top:

                assessment = safety.assess(
                    typed,
                    top["id"],
                )

                flagged = assessment[
                    "requires_second_check"
                ]

                barcode_required = assessment[
                    "requires_barcode_scan"
                ]

                would_be_wrong = (
                    top["id"] != intended["id"]
                    and top["id"] in (a_id, b_id)
                )

                if would_be_wrong:

                    # -------------------------------------------------
                    # High/Critical:
                    # physical barcode verification is required.
                    # -------------------------------------------------

                    if barcode_required:

                        # Consume one RNG draw to preserve the
                        # original simulation sequence.
                        rng.random()

                        barcode_passed = safety.check_barcode(
                            top["id"],
                            intended["id"],
                        )

                        # A barcode mismatch means the wrong candidate
                        # is caught before dispensing.
                        #
                        # Therefore this is NOT counted as a proposed
                        # dispensing error.
                        proposed_error = False

                    # -------------------------------------------------
                    # Medium / ambiguous:
                    # independent second check.
                    # -------------------------------------------------

                    elif flagged:

                        second_check_caught = (
                            rng.random()
                            < SECOND_CHECK_CATCH_RATE
                        )

                        proposed_error = (
                            not second_check_caught
                        )

                    # -------------------------------------------------
                    # No safety friction:
                    # same wrong selection remains an error.
                    # -------------------------------------------------

                    else:
                        proposed_error = True

            pair_breakdown[pair_key]["trials"] += 1

            pair_breakdown[pair_key][
                "baseline_errors"
            ] += int(baseline_error)

            pair_breakdown[pair_key][
                "proposed_errors"
            ] += int(proposed_error)

            trial_log.append(
                {
                    "pair": pair_key,
                    "intended": intended["name"],
                    "typed_input": typed,
                    "baseline_error": baseline_error,
                    "proposed_flagged": flagged,
                    "barcode_required": barcode_required,
                    "barcode_passed": barcode_passed,
                    "second_check_caught": second_check_caught,
                    "proposed_error": proposed_error,
                }
            )

    # ---------------------------------------------------------
    # Control trials
    # ---------------------------------------------------------

    control_trials = 0
    control_false_positive_flags = 0

    for cid in control_ids:

        item = by_id[cid]

        for _ in range(CONTROL_TRIALS_PER_ITEM):

            typed = item["name"]

            results = safety.search(typed)

            top = (
                results[0]
                if results
                else None
            )

            control_trials += 1

            if top:

                assessment = safety.assess(
                    typed,
                    top["id"],
                )

                if assessment[
                    "requires_second_check"
                ]:
                    control_false_positive_flags += 1

    # ---------------------------------------------------------
    # Summary metrics
    # ---------------------------------------------------------

    total_trials = sum(
        v["trials"]
        for v in pair_breakdown.values()
    )

    total_baseline_errors = sum(
        v["baseline_errors"]
        for v in pair_breakdown.values()
    )

    total_proposed_errors = sum(
        v["proposed_errors"]
        for v in pair_breakdown.values()
    )

    baseline_error_rate = (
        total_baseline_errors
        / total_trials
    )

    proposed_error_rate = (
        total_proposed_errors
        / total_trials
    )

    errors_prevented = (
        total_baseline_errors
        - total_proposed_errors
    )

    percent_reduction = (
        errors_prevented
        / total_baseline_errors
        if total_baseline_errors
        else 0.0
    )

    summary = {
        "seed": seed,
        "trials_per_pair": TRIALS_PER_PAIR,
        "second_check_catch_rate_assumption": (
            SECOND_CHECK_CATCH_RATE
        ),
        "target_error_reduction": TARGET_REDUCTION,
        "total_trials": total_trials,
        "baseline_errors": total_baseline_errors,
        "proposed_errors": total_proposed_errors,
        "baseline_error_rate": round(
            baseline_error_rate,
            4,
        ),
        "proposed_error_rate": round(
            proposed_error_rate,
            4,
        ),
        "errors_prevented": errors_prevented,
        "measured_percent_reduction": round(
            percent_reduction,
            4,
        ),
        "target_met": (
            percent_reduction
            >= TARGET_REDUCTION
        ),
        "control_trials": control_trials,
        "control_false_positive_flags": (
            control_false_positive_flags
        ),
        "control_false_positive_rate": (
            round(
                control_false_positive_flags
                / control_trials,
                4,
            )
            if control_trials
            else 0.0
        ),
        "pair_breakdown": pair_breakdown,
    }

    return summary, trial_log


def _bar_chart_svg(
    baseline_rate,
    proposed_rate,
) -> str:

    max_h = 220

    b_h = max(
        2,
        int(
            baseline_rate
            * max_h
            * 3
        ),
    )

    p_h = max(
        2,
        int(
            proposed_rate
            * max_h
            * 3
        ),
    )

    b_h = min(b_h, max_h)
    p_h = min(p_h, max_h)

    base_y = 250

    return f"""<svg viewBox="0 0 360 300" xmlns="http://www.w3.org/2000/svg" font-family="Helvetica, Arial">
  <text x="180" y="24" text-anchor="middle" font-size="15" font-weight="700" fill="#1f1c16">Selection Error Rate: Baseline vs Proposed</text>
  <line x1="40" y1="{base_y}" x2="330" y2="{base_y}" stroke="#333" stroke-width="1.5"/>

  <rect x="90" y="{base_y - b_h}" width="70" height="{b_h}" fill="#c0392b"/>
  <text x="125" y="{base_y + 18}" text-anchor="middle" font-size="12" fill="#1f1c16">Baseline</text>
  <text x="125" y="{base_y - b_h - 8}" text-anchor="middle" font-size="12" fill="#1f1c16">{baseline_rate * 100:.1f}%</text>

  <rect x="220" y="{base_y - p_h}" width="70" height="{p_h}" fill="#1e7e34"/>
  <text x="255" y="{base_y + 18}" text-anchor="middle" font-size="12" fill="#1f1c16">Proposed</text>
  <text x="255" y="{base_y - p_h - 8}" text-anchor="middle" font-size="12" fill="#1f1c16">{proposed_rate * 100:.1f}%</text>
</svg>"""


def main():

    os.makedirs(
        RESULTS_DIR,
        exist_ok=True,
    )

    summary, trial_log = run_experiment()

    # ---------------------------------------------------------
    # experiment_results.json
    # ---------------------------------------------------------

    with open(
        os.path.join(
            RESULTS_DIR,
            "experiment_results.json",
        ),
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            summary,
            f,
            indent=2,
        )

    # ---------------------------------------------------------
    # error_analysis.csv
    # ---------------------------------------------------------

    import csv

    with open(
        os.path.join(
            RESULTS_DIR,
            "error_analysis.csv",
        ),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.writer(f)

        writer.writerow(
            [
                "pair",
                "trials",
                "baseline_errors",
                "proposed_errors",
                "baseline_error_rate",
                "proposed_error_rate",
                "errors_prevented",
            ]
        )

        for pair_key, v in summary[
            "pair_breakdown"
        ].items():

            ber = (
                v["baseline_errors"]
                / v["trials"]
            )

            per = (
                v["proposed_errors"]
                / v["trials"]
            )

            writer.writerow(
                [
                    pair_key,
                    v["trials"],
                    v["baseline_errors"],
                    v["proposed_errors"],
                    round(ber, 4),
                    round(per, 4),
                    (
                        v["baseline_errors"]
                        - v["proposed_errors"]
                    ),
                ]
            )

    # ---------------------------------------------------------
    # trial_log.csv
    # ---------------------------------------------------------

    with open(
        os.path.join(
            RESULTS_DIR,
            "trial_log.csv",
        ),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=list(
                trial_log[0].keys()
            ),
        )

        writer.writeheader()
        writer.writerows(trial_log)

    # ---------------------------------------------------------
    # comparison_chart.svg
    # ---------------------------------------------------------

    with open(
        os.path.join(
            RESULTS_DIR,
            "comparison_chart.svg",
        ),
        "w",
        encoding="utf-8",
    ) as f:

        f.write(
            _bar_chart_svg(
                summary["baseline_error_rate"],
                summary["proposed_error_rate"],
            )
        )

    print(
        json.dumps(
            summary,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
