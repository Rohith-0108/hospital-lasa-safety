# Patient journeys

Both journeys are pre-loaded in the prototype (`web/index.html` -> journey buttons).
Steps marked **[HUMAN REVIEW POINT]** are exactly the points asserted in
`tests/test_safety_engine.py` and logged live in the prototype's audit log.

---

## Journey 1 - OR, STAT pressor (high urgency)

**Context:** Operating Room 3. Patient becomes hypotensive intra-operatively. The
anaesthetist calls out a verbal order under time pressure: *"Give ephedrine, quick!"*
The ODP types `ephed` into the pick system while reaching for the tray.

| Step | System | Human |
|---|---|---|
| 1 | Ranks candidates for `ephed`: **Ephedrine** (target) and **Epinephrine** (confusable partner, Critical risk pair) both score highly on a short, ambiguous prefix | **[HUMAN REVIEW POINT]** ODP reads the ranked list instead of grabbing the first ampoule from muscle memory |
| 2 | Shows risk banner: `Risk level: Critical`, harm-if-wrong text for whichever is selected, packaging side-by-side | **[HUMAN REVIEW POINT]** ODP visually compares packaging/shelf code shown against the tray |
| 3 | Requires barcode scan (mandatory - Critical risk) | **[HUMAN REVIEW POINT]** ODP scans the ampoule in hand; system blocks if it doesn't match the selected candidate |
| 4 | Requires independent second check (mandatory - Critical risk) | **[HUMAN REVIEW POINT]** A second clinician in the room independently confirms name/strength/route out loud, even under time pressure |
| 5 | If checks are incomplete and the team needs to proceed immediately: Override option, requires typed reason, permanently logged | **[HUMAN REVIEW POINT]** Whoever overrides is accountable for a specific, logged reason - never a silent bypass |
| 6 | Enables "Confirm dispense" only once checks (or a logged override) are complete | **[HUMAN REVIEW POINT]** Final sign-off remains a deliberate human action, not automatic |

**Why this journey is high urgency:** every step above still happens, but the
interface is designed so none of them meaningfully slow down a STAT order - the
barcode scan and verbal second check are actions clinical teams already perform
informally; this prototype makes them structured, visible and logged rather than
optional.

---

## Journey 2 - Outpatient, routine refill (low/moderate urgency)

**Context:** Outpatient pharmacy counter. A patient collects a routine 90-day
antihypertensive refill. The prescription reads *"Losartan 50mg, #90, refill"*. The
technician types `loraz` from habit (a common mis-transcription toward the sound-alike
benzodiazepine Lorazepam).

| Step | System | Human |
|---|---|---|
| 1 | Ranks candidates: **Losartan** (target, curated High-risk pair) appears alongside **Lorazepam** even though their raw text similarity is only moderate - because the curated pair list is consulted independently of the live similarity score (see `docs/error_analysis.md`) | **[HUMAN REVIEW POINT]** Technician reads both options rather than trusting the first alphabetical result |
| 2 | Shows risk banner: `Risk level: High`, explains the harm of confusing an antihypertensive with a benzodiazepine | **[HUMAN REVIEW POINT]** Technician re-reads the paper/e-prescription against the on-screen candidate |
| 3 | Requires barcode scan (mandatory - High risk) | **[HUMAN REVIEW POINT]** Technician scans the stock bottle before bagging it |
| 4 | Requires independent second check (mandatory - High risk) | **[HUMAN REVIEW POINT]** A second pharmacist verifies before hand-off to the patient, standard practice for High-risk refills |
| 5 | Enables "Confirm dispense" | **[HUMAN REVIEW POINT]** Pharmacist performs final counselling/hand-off check with the patient |

**Why this journey is lower urgency:** there is no immediate physiological
consequence pending in the next seconds, so the same checks can be performed at a
normal, unhurried pace - the *number* of review points does not change between
journeys, only the time pressure around them. This is a deliberate design choice: the
system does not lower its safety bar for urgency, only its added latency where
possible (e.g. STAT trays are pre-positioned so the barcode scan takes seconds).

---

## Cross-journey observation captured in the audit log

Both journeys start from a **corrupted/partial input** (`ephed`, `loraz`) chosen to
represent exactly the kind of rushed, partial or mis-transcribed entry that causes
real LASA incidents - not a clean, unambiguous query. The prototype's audit log
(right-hand panel) timestamps every review point for both journeys so the full trail
can be inspected end to end.
