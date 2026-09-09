# User / stakeholder validation summary

## Method

A structured walkthrough of the interactive prototype (`web/index.html`) was used as
a **think-aloud review protocol**: a reviewer works through both patient journeys and
all four failure-case demos in both Baseline and Proposed modes, narrating their
reactions, then answers a short structured checklist. This is a lightweight,
prototype-stage validation method - appropriate for this project's stage, not a
substitute for a formal usability study or clinical pilot with real pharmacy staff,
which is listed under "what real validation would still require" below.

## Structured review checklist and findings

| Question | Finding |
|---|---|
| Is the risk information noticeable within 2 seconds of opening a candidate? | Yes - the coloured risk banner and confidence bar are the most visually prominent elements in the detail panel. |
| Does the interface clearly explain *why* an item is risky, not just *that* it is? | Yes - each confusable neighbour lists the specific harm-if-wrong text, not a generic warning. |
| Is it obvious what action is required next at every step? | Mostly yes - the review panel shows outstanding required steps as separate cards; the one gap noted is that Medium-risk items show a banner but no explicit "no further action required" confirmation, which could read as incomplete. **Action:** track as a UI polish item for the next iteration. |
| Does the STAT/high-urgency journey feel like it adds unacceptable delay? | The barcode scan and second check are the same two actions OR staff already perform informally; making them structured did not, in this walkthrough, feel like new work - but this needs confirmation with real OR staff under real time pressure, not a desk review. |
| Is the override path appropriately serious without being unusable? | Yes in this walkthrough - the required typed reason and "REFUSED" / "LOGGED" distinction in the audit log make the override feel deliberate rather than a checkbox to click through. |
| Does the baseline mode plausibly represent how current systems actually behave? | Yes - alphabetical-first-match-wins with zero risk information matches the described behaviour of the legacy pick-list this project is comparing against. |
| Are the packaging illustrations sufficient for the demonstration, given they are original artwork rather than real product photos? | Sufficient for demonstrating the *interface's reaction* to look-alike packaging (shape, layout, minimal differentiation) - explicitly **not** sufficient to validate real-world visual confusability, which depends on actual manufacturer packaging. Flagged in `docs/risk_register.md` R8. |

## Issues raised and resolution status

| Issue | Raised during | Status |
|---|---|---|
| Metformin/Metronidazole pair shows a warning but can still be dispensed without a second check | Walkthrough of Journey-adjacent scenario + confirmed in the measured experiment | **Open** - root-caused and remediation options documented in `docs/error_analysis.md`; deliberately left unfixed so the reported before/after numbers are honest, not tuned post-hoc. |
| Override reason field accepts any non-empty text, including low-effort input | Failure-case demo 4 walkthrough | **Open** - flagged as a future validation item; a real deployment might require a minimum reason length or a structured reason code list, decided with clinical governance input rather than unilaterally in this prototype. |
| Audit log has no persistence across a page reload | Technical walkthrough | **Accepted for prototype scope** - this is a client-side demo; a production system would log to the pharmacy's existing audit/EHR backend, out of scope here. |

## What real validation would still require (explicitly out of scope for this prototype)

- A structured usability session with actual ward, OR and outpatient pharmacy staff,
  not a single desk-based walkthrough.
- Replacing the 88% second-check catch-rate assumption with data from a real pilot
  period (see `docs/stakeholder_assumptions.md`).
- A pharmacy safety committee sign-off on the curated `data/lasa_pairs.csv` risk
  tiers, particularly the Medium/High boundary implicated in the error-analysis gap.
- Integration testing with real barcode-scanning hardware and the hospital's actual
  shelf/inventory system, rather than the simulated string-comparison stand-ins used
  here.
