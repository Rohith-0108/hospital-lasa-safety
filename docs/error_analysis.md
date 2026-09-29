# Error analysis

## Baseline, target, measured result

| | Value |
|---|---|
| **Baseline** selection error rate (current process, simulated) | 40.4% (323/800 trials) |
| **Target** error reduction (stakeholder-set, see `docs/stakeholder_assumptions.md`) | >=90% reduction, i.e. proposed error rate <= ~4.0% |
| **Measured** proposed error rate | 10.1% (81/800 trials) |
| **Measured** reduction | 74.9% |
| **Target met** | No - 15.1 percentage points short of target on the aggregate rate |

## Root cause of the shortfall

The shortfall is **not evenly distributed** - it is concentrated almost entirely in
one pair:

- Excluding Metformin/Metronidazole, the other 7 pairs (700 trials) show 284 baseline
  errors -> 44 proposed errors, an **84.5% reduction**, close to target.
- Metformin/Metronidazole alone (100 trials) shows 39 baseline errors -> 37 proposed
  errors, a **5.1% reduction** - the proposed engine performs almost no better than
  baseline on this pair.

**Why:** `data/lasa_pairs.csv` curates this pair at `reference_risk_tier = Medium`.
`safety_engine.py`'s `requires_second_check` / `requires_barcode_scan` logic only
triggers mandatory verification for `High` and `Critical` risk levels (see
`SafetyEngine.assess`). A Medium-risk flag is *shown* in the UI (risk banner, harm
text) but does not *block* dispensing the way High/Critical does - so in the
simulation, a technician who was going to make the error anyway is shown a warning but
not forced to independently re-verify, and the error frequently still happens.

This is a genuine design gap, not a modelling artefact: the trial log
(`results/trial_log.csv`) shows the engine correctly flags nearly every
Metformin/Metronidazole confusion (`proposed_flagged` is true), it's the *lack of a
mandatory check* at Medium tier that lets the error through.

## Remediation options (not yet implemented - documented for the next iteration)

| Option | Effect | Trade-off |
|---|---|---|
| A. Extend mandatory second-check to Medium-risk items too | Would likely close most of the gap (Metformin/Metronidazole would behave like the other 7 pairs) | Increases friction on a wider set of medicines; risks alert fatigue (see `docs/risk_register.md` R3) - would need to re-run the control (false-positive) trials to confirm friction stays acceptable |
| B. Re-tier Metformin/Metronidazole specifically to High given real incident data | Targeted fix without broadening friction generally | Requires actual local incident-report evidence, not just a design decision - a governance action, not a code change |
| C. Improve the underlying similarity signal so Medium/High boundary is more accurate generally | Systemic improvement | Out of scope for this prototype phase; would need a larger, labelled dataset of real confusions to tune thresholds properly |

**Recommendation for next iteration:** Option A as an immediate mitigation (cheap,
code-only, testable), with Option B as the governance-owned long-term correction once
real incident data exists. This is intentionally left undone in this prototype so the
before/after numbers reported are the actual measured result of the as-built system,
not a result tuned after the fact to hit the target.

## Other findings from the trial log

- **False positives:** 0/80 (0.0%) on control (non-LASA) items - the risk-proportionate
  design is not over-flagging safe picks in this test set.
- **No pair showed the proposed engine performing *worse* than baseline** - the
  minimum improvement across all 8 pairs is +2 errors prevented (Metformin/
  Metronidazole), the maximum is +51 (Insulin Lispro/Glargine).
- **Ambiguous-tie detection** (tested separately in
  `tests/test_safety_engine.py::test_edge_case_ambiguous_tie_forces_disambiguation`)
  is a distinct protection from the pair-based risk tiering and is not fully captured
  in the aggregate trial numbers above, since the simulated `corrupt_name()` inputs
  are engineered to reach a top candidate, not always a literal tie. The interactive
  prototype's "Ambiguous tie" failure-case demo (`web/app.js`, `demoAmbiguousTie`)
  demonstrates this mechanism directly.

## Uncertainty in the measurement itself

- The 88% second-check catch rate (`SECOND_CHECK_CATCH_RATE`) is an assumption (see
  `docs/stakeholder_assumptions.md`); the measured 74.9% reduction moves directionally
  with that assumption - a lower real-world catch rate would show a smaller
  reduction, and vice versa. The experiment is reproducible with different
  assumptions by editing the constant and re-running.
- 800 trials is enough to distinguish the per-pair effects seen here, but is a
  simulation, not a substitute for a real controlled pilot with actual pharmacy staff
  - see `docs/validation_summary.md` for what would be needed to validate this outside
  simulation.
