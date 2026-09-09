# Why look-alike / sound-alike medicines create selection risk

## 1. The three environments compound differently

| Environment | Dominant failure mode | Why |
|---|---|---|
| **Wards** | Verbal/handover confusion, look-alike unit-dose packaging | Nurses often select from a stocked cabinet against a handwritten or verbally relayed order; oral tablets from the same manufacturer are frequently packaged in near-identical blister/box formats. |
| **Operating rooms** | Time pressure, verbal orders, ampoule/vial look-alike | Anaesthetic drugs are drawn up rapidly from trays under time pressure; ampoules are small, labels are brief, and many high-alert drugs (pressors, opioids, paralytics) sit in adjacent trays. |
| **Outpatients** | Sound-alike names at high volume, handwriting | Pharmacists process a high volume of prescriptions; many errors originate in sound-alike drug names misheard or misread from handwriting, then reinforced by an alphabetised pick-list that doesn't distinguish them. |

## 2. Root causes, evidenced by this prototype's data model

1. **Orthographic similarity** - names differing by 1-2 characters or a shared long
   prefix (e.g. *Hydralazine* / *Hydroxyzine*) are visually almost interchangeable at
   a glance, especially on small labels or handwritten orders.
2. **Phonetic similarity** - names that sound alike when spoken (e.g. *Losartan* /
   *Lorazepam*) can be confused in verbal orders or over the phone, even when spelled
   quite differently. `src/similarity.py` models this separately from spelling
   similarity because the two failure modes need different mitigations (large font +
   tall-man lettering for orthographic risk; explicit read-back and second check for
   phonetic risk).
3. **Packaging similarity** - manufacturers reuse container shapes, colours and label
   layouts across a product line; two entirely different drugs from the same
   manufacturer can look identical from an arm's length away. This is independent of
   the *name* similarity and needs a physical check (barcode/shelf), not just a
   smarter search box.
4. **List design that hides risk** - a plain alphabetical pick-list (the baseline in
   this project) sorts *Hydralazine* directly next to *Hydroxyzine* and shows no
   information that would help a rushed clinician tell them apart before selecting.
5. **Silent auto-completion** - many real systems auto-highlight the "best" match for
   a partial or corrupted query. If that guess is wrong, the system has actively
   hidden the ambiguity from the human rather than surfacing it - this is the specific
   failure mode this project's safety engine is built to prevent (see
   `docs/architecture.md`, principle 1: "uncertainty is always shown, never hidden").
6. **Uniform process regardless of stakes** - a routine outpatient refill and a
   STAT intraoperative pressor currently go through the same unweighted selection
   process, even though the harm from a wrong pick is far more acute and immediate in
   the OR. See `docs/patient_journeys.md`.

## 3. Why "just add more alerts" is not sufficient

A naive fix (pop up a warning on every lookup) creates alert fatigue and gets
click-dismissed, which is why the safety engine in this project is deliberately
**risk-proportionate**: Low-risk, unambiguous picks stay fast and frictionless;
High/Critical-risk or ambiguous picks force a mandatory, logged, independent check.
The controlled experiment in `docs/before_after_comparison.md` and
`docs/error_analysis.md` measures whether this design choice actually reduces
selection errors without unacceptable added friction on safe picks (false-positive
rate).
