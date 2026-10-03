
## Residual error identified

The initial risk-aware implementation reduced the measured dispensing error rate,
but residual errors remained concentrated in the Medium-risk
Metformin / Metronidazole pair.

This pair was therefore used as the main error-analysis case for the next
iteration.

## Remediation implemented

The proposed safety engine was strengthened so that higher-risk LASA selections
require explicit safety barriers, including barcode verification for
High/Critical selections.

The simulation preserves the original randomisation sequence so that the
baseline comparison remains reproducible.

## Current measured result

Using seed 42 and 100 trials per LASA pair:

- Total LASA trials: **800**
- Baseline errors: **318 / 800 (39.75%)**
- Proposed errors: **4 / 800 (0.50%)**
- Errors prevented: **314**
- Measured error reduction: **98.74%**
- 90% stakeholder target: **MET**
- Control trials: **80**
- Control false-positive flags: **0 / 80 (0.0%)**

The remaining 4 proposed errors occurred in the
Metformin / Metronidazole pair.

## Pair-level result

| LASA pair | Baseline errors | Proposed errors |
|---|---:|---:|
| Hydralazine / Hydroxyzine | 40 | 0 |
| Vinblastine / Vincristine | 32 | 0 |
| Epinephrine / Ephedrine | 30 | 0 |
| Insulin Lispro / Insulin Glargine | 59 | 0 |
| Hydromorphone / Morphine | 30 | 0 |
| Losartan / Lorazepam | 35 | 0 |
| Chlorpromazine / Chlorpropamide | 58 | 0 |
| Metformin / Metronidazole | 34 | 4 |

## Limitations

The 88% second-check catch rate remains a documented modelling assumption,
not an empirical clinical finding.

The 90% reduction is a stakeholder-set prototype target, not a clinical,
regulatory, or deployment claim.

The simulation is controlled and reproducible; it does not establish
real-world clinical effectiveness.

Further validation should use real pharmacy workflow data, local LASA
incident data, real barcode hardware, and pharmacy safety committee review.

## Future work

- Validate the 88% second-check assumption with real pilot data.
- Investigate the remaining Metformin / Metronidazole errors.
- Validate LASA risk tiers with pharmacy safety stakeholders.
- Test barcode verification using real hospital hardware and inventory data.
