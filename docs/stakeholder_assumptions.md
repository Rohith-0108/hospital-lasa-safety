# Stakeholder assumptions

These are explicit modelling assumptions made to build a measurable prototype without
a live clinical trial. They should be validated or replaced with site-specific data
before any real deployment. Each is flagged where it is used in code/docs.

## Stakeholders assumed

- **Ward nurses** - select from stocked cabinets against written/verbal orders; time
  pressure moderate, volume high.
- **OR anaesthetists/ODPs (operating department practitioners)** - draw up drugs
  rapidly from trays against verbal orders; time pressure severe, error consequence
  immediate and acute.
- **Outpatient pharmacists/technicians** - process high volumes of prescriptions;
  primary risk is sound-alike names at high throughput, less acute time pressure than
  the OR but higher volume of opportunities for error.
- **Pharmacy safety/governance committee** - owns the curated LASA pair list and risk
  tiers, and reviews logged overrides.

## Modelling assumptions (used in `src/simulate_dispensing.py`)

| Assumption | Value used | Where used | Confidence |
|---|---|---|---|
| Independent second-check catch rate | 88% (an independent clinician who performs a genuine second check catches most, not all, of the errors that reach them) | `SECOND_CHECK_CATCH_RATE` | **Assumption, not empirical** - directionally plausible (independent double-checks are a well-established high-reliability-organisation technique) but the specific number is illustrative, not sourced from this site's own audit data. Must be replaced with local audit figures before real deployment. |
| Target error reduction | 90% | `TARGET_REDUCTION` | Stakeholder-set target for this prototype phase, not a regulatory requirement. |
| Corrupted-input generation (`corrupt_name`) | full swap 35% / partial-prefix 35% / single-character drift 30% | `simulate_dispensing.py` | Modelling choice representing three real input-error mechanisms (mis-hearing, rushed partial typing, single mis-transcribed character). Proportions are illustrative; real proportions would need to come from incident-report review. |
| Barcode / shelf checks are reliable once performed | Assumed the scan itself doesn't introduce new error | `safety_engine.py` (`check_barcode`, `check_shelf`) | Reasonable simplification for this prototype; a real deployment should also consider barcode misprints/failures, which is why "barcode scanner offline" is modelled explicitly as failure case 1 in `docs/error_analysis.md`. |
| Control (non-LASA) medicines never need mandatory second-check friction | Verified via `control_false_positive_rate` = 0.0% in the current run | `simulate_dispensing.py` control trial block | Should be re-checked as more medicines are added to the catalogue - see `docs/error_analysis.md`. |

## Scope assumptions

- The prototype covers **medicine name + packaging + shelf selection risk only**. It
  does not model prescribing error, dose calculation error, or administration timing
  error, which are related but separate patient-safety problems.
- The curated pair list (`data/lasa_pairs.csv`) covers 8 pairs / 16 medicines plus 2
  safety-control items, chosen to represent each ward/OR/outpatient area and a range
  of confusion types and risk tiers. A live deployment would need the full hospital
  formulary, likely hundreds to low thousands of items.
- "Dispensing" in this prototype means the point of selection from stock, not
  administration to the patient - the interface targets the pharmacy/nursing/OR
  selection step specifically, per the stated problem scope.
