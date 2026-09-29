/* app.js - client-side mirror of src/similarity.py, src/baseline.py, src/safety_engine.py
   Kept deliberately close to the Python so the demo and the measured experiment
   are provably the same logic, not two different implementations. */

const DATA = window.LASA_DATA;
const MEDICINES = DATA.medicines;
const PAIRS = DATA.pairs;
const PACKAGING = DATA.packaging;
const BY_ID = Object.fromEntries(MEDICINES.map(m => [m.id, m]));

const SIMILARITY_ALERT_THRESHOLD = 0.55;
const TIE_MARGIN = 0.05;
const RISK_ORDER = { Low: 0, Medium: 1, High: 2, Critical: 3 };

// ---------- similarity (mirrors src/similarity.py) ----------
function levenshtein(a, b) {
  a = a.toLowerCase(); b = b.toLowerCase();
  if (a === b) return 0;
  if (!a.length) return b.length;
  if (!b.length) return a.length;
  let prev = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    const cur = [i];
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost);
    }
    prev = cur;
  }
  return prev[b.length];
}
function orthoSim(a, b) {
  if (!a || !b) return 0;
  const d = levenshtein(a, b);
  return 1 - d / Math.max(a.length, b.length);
}
const SOUNDEX_CODES = {
  b: "1", f: "1", p: "1", v: "1",
  c: "2", g: "2", j: "2", k: "2", q: "2", s: "2", x: "2", z: "2",
  d: "3", t: "3", l: "4", m: "5", n: "5", r: "6",
};
function soundex(word) {
  word = (word || "").toLowerCase().replace(/[^a-z]/g, "");
  if (!word) return "0000";
  const first = word[0].toUpperCase();
  let digits = [first];
  let prevCode = SOUNDEX_CODES[word[0]] || "";
  for (let i = 1; i < word.length; i++) {
    const ch = word[i];
    const code = SOUNDEX_CODES[ch] || "";
    if (code && code !== prevCode) digits.push(code);
    if (ch !== "h" && ch !== "w") prevCode = code;
  }
  let res = digits.join("").slice(0, 4);
  while (res.length < 4) res += "0";
  return res;
}
function phoneticSim(a, b) {
  const sa = soundex(a), sb = soundex(b);
  if (sa === sb) return 1.0;
  if (sa.slice(0, 3) === sb.slice(0, 3)) return 0.5;
  return 0.0;
}
function combinedSim(a, b, orthoWeight = 0.6) {
  return Math.round((orthoWeight * orthoSim(a, b) + (1 - orthoWeight) * phoneticSim(a, b)) * 10000) / 10000;
}

// ---------- baseline engine (mirrors src/baseline.py) ----------
function baselineSearch(query) {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  const starts = MEDICINES.filter(m => m.name.toLowerCase().startsWith(q));
  const startIds = new Set(starts.map(m => m.id));
  const contains = MEDICINES.filter(m => m.name.toLowerCase().includes(q) && !startIds.has(m.id));
  const byName = (a, b) => a.name.localeCompare(b.name);
  return [...starts.sort(byName), ...contains.sort(byName)];
}
function baselinePick(query) {
  const r = baselineSearch(query);
  return r.length ? r[0] : null;
}

// ---------- safety engine (mirrors src/safety_engine.py) ----------
const PAIR_LOOKUP = {};
for (const p of PAIRS) {
  (PAIR_LOOKUP[p.id_a] ??= {})[p.id_b] = p;
  (PAIR_LOOKUP[p.id_b] ??= {})[p.id_a] = p;
}
function riskFromSimilarity(score) {
  if (score >= 0.85) return "Critical";
  if (score >= 0.70) return "High";
  if (score >= SIMILARITY_ALERT_THRESHOLD) return "Medium";
  return "Low";
}
function safetySearch(query) {
  const q = query.trim();
  if (!q) return [];
  const scored = [];
  for (const m of MEDICINES) {
    let score = Math.max(combinedSim(q, m.name), combinedSim(q, m.generic));
    if (m.name.toLowerCase().includes(q.toLowerCase()) || m.name.toLowerCase().startsWith(q.toLowerCase())) {
      score = Math.max(score, 0.92);
    }
    if (score > 0.15) scored.push({ score, m });
  }
  scored.sort((x, y) => y.score - x.score);
  return scored.map(({ score, m }) => ({ ...m, match_confidence: Math.round(score * 1000) / 1000 }));
}
function findConfusableNeighbors(candidate) {
  const neighbors = [];
  const knownOthers = PAIR_LOOKUP[candidate.id] || {};
  for (const other of MEDICINES) {
    if (other.id === candidate.id) continue;
    const sim = Math.max(combinedSim(candidate.name, other.name), combinedSim(candidate.generic, other.generic));
    const known = knownOthers[other.id];
    if (known || sim >= SIMILARITY_ALERT_THRESHOLD) {
      const tier = known ? known.reference_risk_tier : riskFromSimilarity(sim);
      neighbors.push({
        id: other.id, name: other.name, similarity: Math.round(sim * 1000) / 1000,
        risk_tier: tier,
        confusion_type: known ? known.confusion_type : "detected-similarity",
        harm_if_confused: other.harm_if_confused,
      });
    }
  }
  neighbors.sort((a, b) => (RISK_ORDER[b.risk_tier] - RISK_ORDER[a.risk_tier]) || (b.similarity - a.similarity));
  return neighbors;
}
function safetyAssess(query, candidateId) {
  const results = safetySearch(query);
  const candidate = BY_ID[candidateId];
  const candResult = results.find(r => r.id === candidateId);
  const confidence = candResult ? candResult.match_confidence : 0.5;
  const neighbors = findConfusableNeighbors(candidate);
  const topNeighbor = neighbors[0] || null;
  const riskLevel = topNeighbor ? topNeighbor.risk_tier : "Low";
  let ambiguousTie = false;
  if (results.length >= 2) {
    ambiguousTie = (results[0].match_confidence - results[1].match_confidence) < TIE_MARGIN && results[0].id !== results[1].id;
  }
  const requiresSecondCheck = riskLevel === "High" || riskLevel === "Critical" || ambiguousTie;
  const requiresBarcode = riskLevel === "High" || riskLevel === "Critical";
  return {
    query, candidate, confidence, risk_level: riskLevel, ambiguous_tie: ambiguousTie,
    tie_candidates: ambiguousTie ? results.slice(0, 3).map(r => r.id) : [],
    confusable_with: neighbors, harm_if_wrong: candidate.harm_if_confused,
    requires_second_check: requiresSecondCheck, requires_barcode_scan: requiresBarcode,
    tallman: candidate.tallman,
  };
}
function checkBarcode(candidateId, scannedId) { return candidateId === scannedId; }
function checkShelf(candidateId, scannedShelf) { return BY_ID[candidateId].shelf_location === scannedShelf; }

// ================= UI STATE & WIRING =================
const state = {
  mode: "proposed", // 'baseline' | 'proposed'
  journey: null,
  query: "",
  results: [],
  selected: null,       // medicine record
  assessment: null,      // safety assessment (proposed mode only)
  barcodeInput: "",
  barcodeOk: null,
  shelfInput: "",
  shelfOk: null,
  secondChecker: "",
  overrideReason: "",
  dispensed: false,
  auditLog: [],
};

const JOURNEYS = {
  or_stat: {
    label: "OR - STAT pressor",
    urgent: true,
    context: "Operating Room 3 - patient hypotensive intra-op. Anaesthetist calls out a verbal order.",
    verbalOrder: "\u201cGive ephedrine, quick!\u201d",
    prefillQuery: "ephed",
    correctId: "M06",
  },
  outpatient_refill: {
    label: "Outpatient - routine refill",
    urgent: false,
    context: "Outpatient pharmacy counter - patient collecting a routine 90-day antihypertensive refill.",
    verbalOrder: "Prescription reads: \u201cLosartan 50mg, #90, refill\u201d",
    prefillQuery: "loraz",
    correctId: "M11",
  },
};

function log(tag, text, cls = "") {
  state.auditLog.push({ time: new Date().toLocaleTimeString(), tag, text, cls });
  renderAuditLog();
}

function resetSelection({ keepQuery = false } = {}) {
  state.results = [];
  state.selected = null;
  state.assessment = null;
  state.barcodeInput = ""; state.barcodeOk = null;
  state.shelfInput = ""; state.shelfOk = null;
  state.secondChecker = "";
  state.overrideReason = "";
  state.dispensed = false;
  if (!keepQuery) state.query = "";
}

function setJourney(key) {
  state.journey = key;
  resetSelection();
  state.auditLog = [];
  const j = JOURNEYS[key];
  state.query = j.prefillQuery;
  log("JOURNEY", `Started: ${j.label}. ${j.context}`);
  log("ORDER", `Order received: ${j.verbalOrder}`);
  runSearch();
  renderAll();
}

function runSearch() {
  state.selected = null;
  state.assessment = null;
  state.dispensed = false;
  if (state.mode === "baseline") {
    state.results = baselineSearch(state.query);
  } else {
    state.results = safetySearch(state.query).slice(0, 6);
  }
}

function selectCandidate(id) {
  state.selected = BY_ID[id];
  state.barcodeInput = ""; state.barcodeOk = null;
  state.shelfInput = ""; state.shelfOk = null;
  state.secondChecker = "";
  state.dispensed = false;
  if (state.mode === "baseline") {
    log("SELECT", `Baseline auto-selected: ${state.selected.name} (${state.selected.strength}) - no risk information shown.`);
  } else {
    state.assessment = safetyAssess(state.query, id);
    log("SELECT", `Candidate opened: ${state.selected.name} (${state.selected.strength}) - confidence ${(state.assessment.confidence * 100).toFixed(0)}%`);
    log("RISK", `Risk level: ${state.assessment.risk_level}${state.assessment.ambiguous_tie ? " (ambiguous tie detected)" : ""}`, "review");
  }
  renderAll();
}

function tryDispenseBaseline() {
  state.dispensed = true;
  log("DISPENSE", `Dispensed ${state.selected.name} - single click, no verification step (baseline).`, "block");
  renderAll();
}

function submitBarcode() {
  state.barcodeOk = checkBarcode(state.selected.id, state.barcodeInput.trim());
  if (state.barcodeOk) {
    log("REVIEW", `Barcode scan matched ${state.selected.name} (human review point).`, "review");
  } else {
    log("BLOCK", `Barcode scan MISMATCH - scanned code does not match ${state.selected.name}. Dispensing blocked.`, "block");
  }
  renderAll();
}
function submitShelf() {
  state.shelfOk = checkShelf(state.selected.id, state.shelfInput.trim());
  if (state.shelfOk) {
    log("REVIEW", `Shelf location confirmed: ${state.shelfInput.trim()} (human review point).`, "review");
  } else {
    log("BLOCK", `Shelf mismatch - item scanned from ${state.shelfInput.trim() || "(empty)"}, expected ${state.selected.shelf_location}. Flagged for physical re-check.`, "block");
  }
  renderAll();
}
function submitSecondChecker() {
  if (state.secondChecker.trim()) {
    log("REVIEW", `Independent second check completed by "${state.secondChecker.trim()}" (human review point).`, "review");
  }
  renderAll();
}
function attemptOverride() {
  const reason = prompt("This medicine is High/Critical risk and required checks are incomplete.\nOverride is logged and requires a reason:");
  if (reason === null) return;
  if (!reason.trim()) {
    log("BLOCK", "Override attempted with no reason given - override refused.", "block");
  } else {
    log("BLOCK", `OVERRIDE LOGGED: "${reason.trim()}" - dispensing proceeded without completed checks. Flagged for supervisor review.`, "block");
  }
  renderAll();
}

function canDispenseProposed() {
  if (!state.assessment) return false;
  if (!state.assessment.requires_second_check && !state.assessment.requires_barcode_scan) return true;
  const secondOk = !state.assessment.requires_second_check || state.secondChecker.trim().length > 0;
  const barcodeOk = !state.assessment.requires_barcode_scan || state.barcodeOk === true;
  return secondOk && barcodeOk;
}
function tryDispenseProposed() {
  if (!canDispenseProposed()) return;
  state.dispensed = true;
  log("DISPENSE", `Dispensed ${state.selected.name} - all required checks completed (human review point: final sign-off).`, "review");
  renderAll();
}

// ---------- failure-case demo triggers ----------
function demoAmbiguousTie() {
  setJourney(state.journey || "or_stat");
  state.query = "Vin";
  log("DEMO", "Failure case 1: ambiguous tie - typing a short prefix common to two critical-risk chemotherapy drugs.");
  runSearch(); renderAll();
}
function demoBarcodeMismatch() {
  setJourney(state.journey || "or_stat");
  state.query = "Morphine";
  runSearch();
  selectCandidate("M10");
  state.barcodeInput = "M09"; // deliberately scan the wrong (hydromorphone) vial
  submitBarcode();
  log("DEMO", "Failure case 2: technician believed they picked Morphine, but the physical vial scanned is Hydromorphone.");
}
function demoShelfMismatch() {
  setJourney(state.journey || "or_stat");
  state.query = "Insulin Lispro";
  runSearch();
  selectCandidate("M07");
  state.shelfInput = "W-05-B"; // Glargine's shelf, not Lispro's
  submitShelf();
  log("DEMO", "Failure case 3: item was restocked in the neighbouring bin - shelf scan does not match expected location.");
}
function demoOverride() {
  setJourney(state.journey || "or_stat");
  state.query = "Hydromorphone";
  runSearch();
  selectCandidate("M09");
  log("DEMO", "Failure case 4: user attempts to bypass required checks under time pressure - override must be reasoned and logged, never silent.");
  attemptOverride();
}

// ================= RENDERING =================
const el = (sel) => document.querySelector(sel);

const ICONS = {
  pill: '<svg class="r-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><rect x="4" y="9" width="16" height="7.5" rx="3.75" transform="rotate(-45 12 12)"/><line x1="12" y1="8" x2="12" y2="16" transform="rotate(-45 12 12)"/></svg>',
  search: '<svg class="e-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="10" cy="10" r="6"/><line x1="14.5" y1="14.5" x2="20" y2="20"/></svg>',
  pointer: '<svg class="e-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3l4 16 2.5-6.5L19 10z"/></svg>',
  clipboard: '<svg class="e-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V3a1 1 0 011-1h4a1 1 0 011 1v1"/></svg>',
  checkCircle: '<svg class="banner-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.5 2.5L16 9.5"/></svg>',
  alertCircle: '<svg class="banner-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="8" x2="12" y2="13"/><circle cx="12" cy="16.3" r="0.4" fill="currentColor" stroke="none"/></svg>',
  alertTriangle: '<svg class="banner-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 4L2.5 20h19L12 4z"/><line x1="12" y1="10" x2="12" y2="14.5"/><circle cx="12" cy="17.3" r="0.4" fill="currentColor" stroke="none"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="width:13px;height:13px"><path d="M5 12.5l4.5 4.5L19 7"/></svg>',
  x: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="width:12px;height:12px"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg>',
};
const RISK_BANNER_ICON = { Low: ICONS.checkCircle, Medium: ICONS.alertCircle, High: ICONS.alertTriangle, Critical: ICONS.alertTriangle };

function renderAll() {
  renderJourneyBar();
  renderOrderPanel();
  renderSearchPanel();
  renderDetailPanel();
  renderReviewPanel();
}

function renderJourneyBar() {
  document.querySelectorAll(".journey-btn").forEach(b => {
    const active = b.dataset.journey === state.journey;
    b.classList.toggle("active", active);
    b.setAttribute("aria-pressed", String(active));
  });
  document.querySelectorAll(".mode-toggle button").forEach(b => {
    const active = b.dataset.mode === state.mode;
    b.classList.toggle("active", active);
    b.setAttribute("aria-pressed", String(active));
  });
}

function renderOrderPanel() {
  const j = state.journey ? JOURNEYS[state.journey] : null;
  const box = el("#order-summary");
  if (!j) {
    box.innerHTML = `
      <ol class="onboard-steps">
        <li><span class="num">1</span> Pick a patient journey above (or a failure-case demo) to load an order.</li>
        <li><span class="num">2</span> Search by the name heard or typed, then select a candidate.</li>
        <li><span class="num">3</span> Complete whatever verification the risk level requires, then dispense.</li>
      </ol>`;
    return;
  }
  box.innerHTML = `
    ${j.urgent ? '<span class="urgent-flag">STAT</span>' : ""}
    <b>${j.label}</b><br>${j.context}<br>
    <span style="font-style:italic">${j.verbalOrder}</span>`;
}

function renderSearchPanel() {
  const input = el("#search-input");
  if (document.activeElement !== input) input.value = state.query;
  const list = el("#result-list");
  if (!state.journey) {
    list.innerHTML = `<p class="empty-state">${ICONS.pointer}<span>Pick a patient journey above to load an order.</span></p>`;
    return;
  }
  if (!state.results.length) {
    list.innerHTML = `<p class="empty-state">${ICONS.search}<span>No matches for "${state.query}".</span></p>`;
    return;
  }
  list.innerHTML = state.results.map(r => `
    <div class="result-item ${state.selected && state.selected.id === r.id ? "selected" : ""}">
      <div class="r-main">
        <div class="r-name-row">${ICONS.pill}<strong>${r.name}</strong> <span style="color:var(--ink-soft);font-size:12.5px">${r.strength}, ${r.form}</span></div>
        ${state.mode === "proposed" ? `
          <div class="conf-row">
            <span class="conf-chip">${(r.match_confidence * 100).toFixed(0)}% match</span>
            <div class="mini-bar-track"><div class="mini-bar-fill" style="width:${(r.match_confidence * 100).toFixed(0)}%"></div></div>
          </div>` : ""}
      </div>
      <button data-select="${r.id}" aria-label="Select ${r.name}, ${r.strength} ${r.form}">Select</button>
    </div>`).join("");
  list.querySelectorAll("[data-select]").forEach(btn => {
    btn.addEventListener("click", () => selectCandidate(btn.dataset.select));
  });
}

function renderDetailPanel() {
  const panel = el("#detail-panel-body");
  if (!state.selected) { panel.innerHTML = `<p class="empty-state">${ICONS.clipboard}<span>Select a candidate to view packaging, shelf location and (in Proposed mode) its risk assessment.</span></p>`; return; }
  const m = state.selected;
  let html = `
    <div class="candidate-card">
      <div class="packaging">${PACKAGING[m.id]}</div>
      <div class="candidate-meta">
        <div class="name">${state.mode === "proposed" ? m.tallman : m.name}</div>
        <div>${m.strength} &middot; ${m.form} &middot; ${m.route}</div>
        <div>Shelf: <span class="shelf-code">${m.shelf_location}</span> &middot; ${m.ward_area}</div>
      </div>
    </div>`;
  if (state.mode === "proposed" && state.assessment) {
    const a = state.assessment;
    html += `
      <div class="confidence-bar-track"><div class="confidence-bar-fill" style="width:${(a.confidence * 100).toFixed(0)}%"></div></div>
      <div style="font-size:12.5px;color:var(--ink-soft)">Match confidence: ${(a.confidence * 100).toFixed(0)}% - this is a system estimate, not a certainty.</div>
      <div class="risk-banner risk-${a.risk_level}">
        ${RISK_BANNER_ICON[a.risk_level] || ""}
        <span>
          <strong>Risk level: ${a.risk_level}</strong><br>
          ${a.ambiguous_tie ? "Multiple candidates scored nearly identically - the system will not presume which one you meant.<br>" : ""}
          <span style="font-size:12.5px">If the wrong item is dispensed: ${a.harm_if_wrong}</span>
        </span>
      </div>`;
    if (a.confusable_with.length) {
      html += `<div class="confusable-list"><strong style="font-size:12.5px">Could be confused with:</strong>`;
      a.confusable_with.forEach(n => {
        html += `<div class="neighbor"><span class="tier-tag tier-${n.risk_tier}">${n.risk_tier}</span>
          <strong>${n.name}</strong> - similarity ${(n.similarity * 100).toFixed(0)}% (${n.confusion_type})<br>
          <span style="font-size:12px;color:var(--ink-soft)">${n.harm_if_confused}</span></div>`;
      });
      html += `</div>`;
    }
    html += `<div class="uncertainty-note">The system shows its confidence and every plausible alternative instead of silently picking one - the human decides with full information, not the algorithm alone.</div>`;
  }
  panel.innerHTML = html;
}

function renderReviewPanel() {
  const panel = el("#review-panel-body");
  if (!state.selected) { panel.innerHTML = `<p class="empty-state">${ICONS.clipboard}<span>Human review steps for the selected item will appear here.</span></p>`; return; }

  if (state.mode === "baseline") {
    panel.innerHTML = `
      <div class="review-step"><div class="step-marker">1</div><div class="step-body"><h3>Confirm &amp; dispense</h3>
        <p class="hint">Baseline has no confidence score, no risk flag and no mandatory second check - the technician can dispense on a single click regardless of how confusable the item is.</p>
        <button class="btn-primary" id="btn-dispense-baseline" ${state.dispensed ? "disabled" : ""}>${state.dispensed ? "Dispensed" : "Confirm dispense"}</button>
      </div></div>
      ${state.dispensed ? `<div class="dispensed-banner">${ICONS.alertTriangle}Dispensed with zero verification steps.</div>` : ""}`;
    const btn = el("#btn-dispense-baseline");
    if (btn) btn.addEventListener("click", tryDispenseBaseline);
    return;
  }

  const a = state.assessment;
  let html = `<div class="step-list">`;
  let stepNum = 1;
  if (a.requires_barcode_scan) {
    const marker = state.barcodeOk === true ? ICONS.check : state.barcodeOk === false ? ICONS.x : String(stepNum);
    html += `
      <div class="review-step ${state.barcodeOk === true ? "done" : state.barcodeOk === false ? "blocked" : ""}">
        <div class="step-marker">${marker}</div>
        <div class="step-body">
        <h3>Scan packaging barcode</h3>
        <p class="hint">Required because risk level is ${a.risk_level}. Confirms the physical item matches the on-screen selection.</p>
        <label class="visually-hidden" for="barcode-input">Scan or type stock ID</label>
        <input id="barcode-input" aria-label="Scan or type stock ID" placeholder="Scan or type stock ID (try: ${a.candidate.id})" value="${state.barcodeInput}">
        <button class="btn-primary" id="btn-barcode">Submit scan</button>
        ${state.barcodeOk === true ? '<div class="hint" style="color:var(--green);margin-top:4px">Match confirmed.</div>' : ""}
        ${state.barcodeOk === false ? '<div class="hint" style="color:var(--red-deep);margin-top:4px">Mismatch - wrong item detected. Do not dispense.</div>' : ""}
        </div>
      </div>`;
    stepNum++;
  }
  if (a.requires_second_check) {
    const marker = state.secondChecker.trim() ? ICONS.check : String(stepNum);
    html += `
      <div class="review-step ${state.secondChecker.trim() ? "done" : ""}">
        <div class="step-marker">${marker}</div>
        <div class="step-body">
        <h3>Independent second check</h3>
        <p class="hint">${a.ambiguous_tie ? "Required because two candidates were nearly indistinguishable." : `Required because risk level is ${a.risk_level}.`} A second clinician independently confirms name, strength and route.</p>
        <label class="visually-hidden" for="second-checker-input">Second checker name or ID</label>
        <input id="second-checker-input" aria-label="Second checker name or ID" placeholder="Second checker name/ID" value="${state.secondChecker}">
        <button class="btn-primary" id="btn-second-check">Confirm second check</button>
        </div>
      </div>`;
    stepNum++;
  }
  html += `
    <div class="review-step">
      <div class="step-marker">${state.dispensed ? ICONS.check : stepNum}</div>
      <div class="step-body">
      <h3>Final step: confirm &amp; dispense</h3>
      <button class="btn-primary" id="btn-dispense-proposed" ${canDispenseProposed() && !state.dispensed ? "" : "disabled"}>${state.dispensed ? "Dispensed" : "Confirm dispense"}</button>
      ${!canDispenseProposed() && !state.dispensed ? `<button class="btn-danger" id="btn-override" style="margin-left:8px">Override (logged)</button>` : ""}
      </div>
    </div>
  </div>`;
  if (state.dispensed) {
    html += `<div class="dispensed-banner">${ICONS.checkCircle}Dispensed - ${a.risk_level} risk item, all required checks completed and logged.</div>`;
  }

  panel.innerHTML = html;
  const bc = el("#barcode-input"); if (bc) bc.addEventListener("input", e => state.barcodeInput = e.target.value);
  const bcBtn = el("#btn-barcode"); if (bcBtn) bcBtn.addEventListener("click", submitBarcode);
  const scInput = el("#second-checker-input"); if (scInput) scInput.addEventListener("input", e => state.secondChecker = e.target.value);
  const scBtn = el("#btn-second-check"); if (scBtn) scBtn.addEventListener("click", submitSecondChecker);
  const dispBtn = el("#btn-dispense-proposed"); if (dispBtn) dispBtn.addEventListener("click", tryDispenseProposed);
  const ovBtn = el("#btn-override"); if (ovBtn) ovBtn.addEventListener("click", attemptOverride);
}

function renderAuditLog() {
  const box = el("#audit-log");
  if (!box) return;
  box.innerHTML = state.auditLog.slice().reverse().map(e =>
    `<div class="entry ${e.cls}"><span class="tag">[${e.time}] ${e.tag}</span> - ${e.text}</div>`
  ).join("") || `<p class="empty-state">No activity yet.</p>`;
}

// ---------- top-level event wiring ----------
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".mode-toggle button").forEach(b => {
    b.addEventListener("click", () => {
      state.mode = b.dataset.mode;
      resetSelection({ keepQuery: true });
      if (state.journey) runSearch();
      renderAll();
    });
  });
  document.querySelectorAll(".journey-btn").forEach(b => {
    b.addEventListener("click", () => setJourney(b.dataset.journey));
  });
  el("#search-input").addEventListener("input", e => {
    state.query = e.target.value;
    runSearch();
    renderAll();
  });
  el("#btn-demo-tie").addEventListener("click", demoAmbiguousTie);
  el("#btn-demo-barcode").addEventListener("click", demoBarcodeMismatch);
  el("#btn-demo-shelf").addEventListener("click", demoShelfMismatch);
  el("#btn-demo-override").addEventListener("click", demoOverride);

  renderAll();
  renderAuditLog();
});
