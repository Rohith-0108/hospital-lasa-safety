## Remediation options

| Option | Effect | Trade-off | Status |
|---|---|---|---|
| A. Extend mandatory second-check to Medium-risk items too | Applies mandatory second-check friction to Medium, High, and Critical LASA risks. This substantially reduces the Metformin / Metronidazole residual errors. | Increases friction on a wider set of medicines; control trials must be re-run to monitor alert burden. | **Implemented and tested** |
| B. Re-tier Metformin/Metronidazole specifically to High given real incident data | Targeted fix without broadening friction generally | Requires actual local incident-report evidence and pharmacy governance approval. | Not implemented |
| C. Improve the underlying similarity signal so Medium/High boundary is more accurate generally | Systemic improvement | Would need a larger labelled dataset of real medication confusions. | Future work |
| D. Model barcode verification as an independent safety barrier | Could provide an additional safety layer for High/Critical selections | Requires an explicit, evidence-based barcode detection assumption and separate validation; current simulation does not model barcode as an independent catch mechanism. | Future work |

### Current measured result

After implementing Option A, the controlled simulation changed from **74.92% to 84.91% error reduction**. Proposed errors decreased from **81/800 to 48/800**, while the control false-positive rate remained **0/80 (0.0%)**.

The **90% stakeholder target is not yet met**. The remaining gap should be addressed through further validated safety-engine improvements rather than by changing simulation assumptions solely to reach the target.

The 88% second-check catch rate remains a documented modelling assumption, not an empirical clinical finding.