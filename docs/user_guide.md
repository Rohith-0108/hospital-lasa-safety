# User guide - interactive prototype

Open `web/index.html` in any modern browser. No install, server, or internet
connection is required (fonts will fall back gracefully offline).

## 1. Choose a mode

Top-right toggle:
- **Baseline (current process)** - plain pick-list, no risk information, one-click
  dispense. Represents the current-state process being replaced.
- **Proposed safety interface** - full risk assessment, tall-man lettering,
  confusable-neighbour list, and risk-proportionate mandatory checks. This is the
  default on load.

## 2. Choose a patient journey

Journey bar, second row:
- **OR - STAT pressor (high urgency)** - loads a time-pressured intraoperative
  scenario with a pre-filled, deliberately ambiguous query (`ephed`).
- **Outpatient - routine refill (low urgency)** - loads a routine prescription-refill
  scenario with a pre-filled, deliberately ambiguous query (`loraz`).

Selecting a journey resets the audit log and shows the order context at the top of
the leftmost panel.

## 3. Search and select

Type into the search box (or use the pre-filled query). The result list shows every
candidate above a relevance threshold; in Proposed mode each shows a live confidence
percentage. Click **Select** on a candidate to open it in the centre panel.

## 4. Read the risk assessment (Proposed mode)

The centre panel shows: original packaging artwork, tall-man name, strength/form/
route, shelf location, a confidence bar, a colour-coded risk banner (Low/Medium/High/
Critical), and - if any exist - the specific medicines this one could be confused
with, each with its own harm-if-wrong explanation. This panel never hides
uncertainty: if the system isn't sure, that is shown, not resolved silently.

## 5. Complete required review steps (Proposed mode, High/Critical risk only)

The right-hand panel lists exactly which steps are required for this specific item:
- **Barcode scan** - type the medicine ID shown as a hint (in a real deployment this
  would be a physical barcode scan) to simulate confirming the physical item.
- **Independent second check** - type a name/ID to simulate a second clinician's
  verification.

The **Confirm dispense** button only becomes enabled once all required steps for that
item's risk level are complete. If you want to proceed without completing them, the
**Override (logged)** button is available - it requires a typed reason and is always
recorded in the audit log, never silent.

## 6. Watch the audit log

Every action - selection, risk flag, review step, block, override, and final dispense
- is timestamped in the audit log at the bottom-right, most recent first. This is the
same trail referenced in `docs/patient_journeys.md`.

## 7. Try the failure-case demos

Journey bar, right-hand group - each button jumps straight to a specific failure
scenario:
1. **Ambiguous tie** - types a short prefix common to two Critical-risk chemotherapy
   drugs; the system refuses to presume which one you meant.
2. **Barcode mismatch** - simulates scanning the wrong physical vial; dispensing is
   blocked even though the on-screen name looked right.
3. **Shelf mismatch** - simulates an item restocked in the wrong bin.
4. **Override under pressure** - simulates a technician trying to bypass required
   checks; shows the mandatory, logged reason prompt.

## Notes

- The web prototype's matching logic is a byte-for-byte-equivalent JavaScript port of
  `src/similarity.py`, `src/baseline.py` and `src/safety_engine.py` - cross-checked in
  the repository build process, not two independently-written implementations that
  could silently diverge.
- All medicine names are real; all packaging artwork is original illustration created
  for this project - see the footer disclaimer in the app itself.
