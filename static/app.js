const sampleNote = `Pt is a 58 y/o male with Type 2 Diabetes.
Currently taking Metformin 1000mg BID.
HbA1c today is 7.8%, previously 7.2% three months ago.
Denies chest pain.
HTN treated with Lisinopril 20mg daily.
BP today 145/92.
Plan: continue Metformin and follow up in 3 months.`;

const state = {
  result: null,
  decisions: new Map(),
  auditTrail: [],
  filter: "all",
};

const els = {
  apiStatus: document.querySelector("#apiStatus"),
  noteDate: document.querySelector("#noteDate"),
  noteText: document.querySelector("#noteText"),
  runButton: document.querySelector("#runButton"),
  sampleButton: document.querySelector("#sampleButton"),
  clearButton: document.querySelector("#clearButton"),
  exportButton: document.querySelector("#exportButton"),
  warnings: document.querySelector("#warnings"),
  candidateList: document.querySelector("#candidateList"),
  candidateCount: document.querySelector("#candidateCount"),
  approvedCount: document.querySelector("#approvedCount"),
  queueSubtitle: document.querySelector("#queueSubtitle"),
  highlightedNote: document.querySelector("#highlightedNote"),
  compliancePanel: document.querySelector("#compliancePanel"),
  auditTrail: document.querySelector("#auditTrail"),
  jsonOutput: document.querySelector("#jsonOutput"),
  kpiCandidates: document.querySelector("#kpiCandidates"),
  kpiApproved: document.querySelector("#kpiApproved"),
  kpiReviewLoad: document.querySelector("#kpiReviewLoad"),
  kpiPhi: document.querySelector("#kpiPhi"),
  tabs: document.querySelectorAll(".tab"),
};

async function checkApi() {
  try {
    const response = await fetch("/health");
    els.apiStatus.textContent = response.ok ? "API online" : "API issue";
  } catch {
    els.apiStatus.textContent = "API offline";
  }
}

function escapeHtml(value = "") {
  return String(value).replace(/[&<>"']/g, (char) => {
    const map = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };
    return map[char];
  });
}

async function analyzeNote() {
  els.runButton.disabled = true;
  els.runButton.textContent = "Analyzing";
  try {
    const response = await fetch("/api/suggest-codes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        raw_note_text: els.noteText.value,
        note_date: els.noteDate.value || null,
      }),
    });

    if (!response.ok) throw new Error(`Request failed: ${response.status}`);

    state.result = await response.json();
    state.decisions = new Map(
      state.result.code_candidates.map((candidate) => [candidate.id, candidate.status])
    );
    state.auditTrail = [];
    appendLocalAudit("analysis_completed", "System generated candidate codes.");
    render();
  } catch (error) {
    els.candidateList.innerHTML = `<div class="warning">${escapeHtml(error.message)}</div>`;
  } finally {
    els.runButton.disabled = false;
    els.runButton.textContent = "Analyze Note";
  }
}

function filteredCandidates() {
  if (!state.result) return [];
  if (state.filter === "all") return state.result.code_candidates;
  if (state.filter === "risk") {
    return state.result.code_candidates.filter(
      (candidate) => candidate.negated || candidate.confidence < 0.7 || candidate.code.includes("/")
    );
  }
  return state.result.code_candidates.filter((candidate) => candidate.code_system === state.filter);
}

function reviewedCandidates() {
  if (!state.result) return [];
  return state.result.code_candidates.map((candidate) => ({
    ...candidate,
    status: state.decisions.get(candidate.id) || candidate.status,
  }));
}

function appendLocalAudit(action, note, candidate = null) {
  state.auditTrail.unshift({
    action,
    note,
    candidate_id: candidate?.id || null,
    code: candidate?.code || null,
    code_system: candidate?.code_system || null,
    status: candidate ? state.decisions.get(candidate.id) : null,
    reviewer: "demo.coder",
    created_at: new Date().toISOString(),
  });
}

async function recordAudit(candidate, decision) {
  appendLocalAudit(`candidate_${decision}`, `${candidate.description} marked ${decision}.`, candidate);
  try {
    await fetch("/api/audit-events", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: `candidate_${decision}`,
        candidate_id: candidate.id,
        code: candidate.code,
        code_system: candidate.code_system,
        status: decision,
        reviewer: "demo.coder",
        note: candidate.description,
      }),
    });
  } catch {
    appendLocalAudit("audit_sync_failed", "Local event recorded but API audit sync failed.");
  }
}

function setDecision(id, decision) {
  const candidate = state.result?.code_candidates.find((item) => item.id === id);
  if (!candidate) return;
  state.decisions.set(id, decision);
  recordAudit(candidate, decision);
  render();
}

function renderWarnings() {
  const warnings = state.result?.warnings || [];
  els.warnings.innerHTML = warnings
    .map((warning) => `<div class="warning">${escapeHtml(warning)}</div>`)
    .join("");
}

function renderKpis() {
  const candidates = state.result?.code_candidates || [];
  const approved = Array.from(state.decisions.values()).filter((value) => value === "approved").length;
  const riskSummary = state.result?.risk_summary;

  els.kpiCandidates.textContent = candidates.length;
  els.kpiApproved.textContent = approved;
  els.kpiReviewLoad.textContent = riskSummary?.estimated_review_load || "-";
  els.kpiPhi.textContent = riskSummary?.phi_risk_count ?? 0;
  els.candidateCount.textContent = `${candidates.length} candidates`;
  els.approvedCount.textContent = `${approved} approved`;
  els.queueSubtitle.textContent = state.result
    ? `${riskSummary.requires_review_count} require coder review, processed ${state.result.processed_at}`
    : "No analysis yet";
}

function renderCandidates() {
  const candidates = filteredCandidates();

  if (!state.result) {
    els.candidateList.innerHTML = `<div class="empty-state">Analyze a note to generate candidate codes.</div>`;
    return;
  }

  if (!candidates.length) {
    els.candidateList.innerHTML = `<div class="empty-state">No candidates for this filter.</div>`;
    return;
  }

  els.candidateList.innerHTML = candidates
    .map((candidate) => {
      const decision = state.decisions.get(candidate.id) || "needs_review";
      const systemClass = candidate.code_system.toLowerCase().replace(/[^a-z0-9]/g, "");
      const riskBadges = [
        candidate.negated ? "Negated" : null,
        candidate.confidence < 0.7 ? "Low confidence" : null,
        candidate.code.includes("/") ? "Code range" : null,
      ].filter(Boolean);

      return `
        <article class="candidate ${decision}">
          <div class="candidate-title">
            <div>
              <strong>${escapeHtml(candidate.description)}</strong>
              <p>${escapeHtml(candidate.category)} | confidence ${(candidate.confidence * 100).toFixed(0)}%</p>
            </div>
            <span class="code-pill ${systemClass}">${escapeHtml(candidate.code_system)} ${escapeHtml(candidate.code)}</span>
          </div>
          <div class="badge-row">
            ${riskBadges.map((badge) => `<span class="risk-badge">${escapeHtml(badge)}</span>`).join("")}
            <span class="status-badge">${escapeHtml(decision.replace("_", " "))}</span>
          </div>
          <div class="evidence">Evidence: ${escapeHtml(candidate.evidence.text)}</div>
          <p>${escapeHtml(candidate.validation_reason)} ${escapeHtml(candidate.coding_note)}</p>
          <div class="review-actions">
            <button class="approve" type="button" data-decision="approved" data-id="${escapeHtml(candidate.id)}">Approve</button>
            <button class="reject" type="button" data-decision="rejected" data-id="${escapeHtml(candidate.id)}">Reject</button>
            <button class="secondary" type="button" data-decision="needs_review" data-id="${escapeHtml(candidate.id)}">Needs Review</button>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderHighlightedNote() {
  if (!state.result) {
    els.highlightedNote.textContent = "";
    return;
  }

  const note = state.result.clean_text;
  const ranges = [
    ...state.result.code_candidates.map((candidate) => ({ ...candidate.evidence, className: "code-mark" })),
    ...state.result.phi_findings.map((finding) => ({ ...finding, className: "phi-mark" })),
  ].sort((a, b) => a.start - b.start);

  let cursor = 0;
  let html = "";
  for (const range of ranges) {
    if (range.start < cursor) continue;
    html += escapeHtml(note.slice(cursor, range.start));
    html += `<mark class="${range.className}">${escapeHtml(note.slice(range.start, range.end))}</mark>`;
    cursor = range.end;
  }
  html += escapeHtml(note.slice(cursor));
  els.highlightedNote.innerHTML = html;
}

function renderCompliance() {
  if (!state.result) {
    els.compliancePanel.innerHTML = `<div class="empty-state">Compliance posture appears after analysis.</div>`;
    return;
  }

  const posture = state.result.compliance_posture;
  const controls = posture.security_controls_needed_for_production
    .map((control) => `<li>${escapeHtml(control)}</li>`)
    .join("");
  const phiFindings = state.result.phi_findings.length
    ? state.result.phi_findings
        .map((finding) => `<li>${escapeHtml(finding.type)}: ${escapeHtml(finding.text)}</li>`)
        .join("")
    : "<li>No simple PHI pattern flags detected.</li>";

  els.compliancePanel.innerHTML = `
    <div class="compliance-grid">
      <div><span>Mode</span><strong>${escapeHtml(posture.mode)}</strong></div>
      <div><span>PHI storage</span><strong>${escapeHtml(posture.phi_storage)}</strong></div>
      <div><span>BAA for PHI</span><strong>${posture.baa_required_for_phi_use ? "Required" : "Review"}</strong></div>
      <div><span>Human review</span><strong>${posture.human_review_required ? "Required" : "Optional"}</strong></div>
    </div>
    <h3>PHI pattern findings</h3>
    <ul>${phiFindings}</ul>
    <h3>Production controls to implement</h3>
    <ul>${controls}</ul>
  `;
}

function renderAuditTrail() {
  if (!state.auditTrail.length) {
    els.auditTrail.innerHTML = `<div class="empty-state">Review actions will appear here.</div>`;
    return;
  }

  els.auditTrail.innerHTML = state.auditTrail
    .slice(0, 12)
    .map(
      (event) => `
        <div class="audit-event">
          <strong>${escapeHtml(event.action)}</strong>
          <span>${escapeHtml(event.created_at)}</span>
          <p>${escapeHtml(event.note)}</p>
        </div>
      `
    )
    .join("");
}

function renderJson() {
  if (!state.result) {
    els.jsonOutput.textContent = "{}";
    return;
  }

  els.jsonOutput.textContent = JSON.stringify(
    {
      ...state.result,
      reviewed_code_candidates: reviewedCandidates(),
      audit_trail: state.auditTrail,
    },
    null,
    2
  );
}

function exportReview() {
  if (!state.result) return;
  const payload = {
    exported_at: new Date().toISOString(),
    reviewed_code_candidates: reviewedCandidates(),
    risk_summary: state.result.risk_summary,
    phi_findings: state.result.phi_findings,
    audit_trail: state.auditTrail,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `clinical-coder-review-${Date.now()}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

function render() {
  renderWarnings();
  renderKpis();
  renderCandidates();
  renderHighlightedNote();
  renderCompliance();
  renderAuditTrail();
  renderJson();
}

els.runButton.addEventListener("click", analyzeNote);
els.sampleButton.addEventListener("click", () => {
  els.noteText.value = sampleNote;
  els.noteDate.value = "2024-01-15";
});
els.clearButton.addEventListener("click", () => {
  els.noteText.value = "";
  state.result = null;
  state.decisions = new Map();
  state.auditTrail = [];
  render();
});
els.exportButton.addEventListener("click", exportReview);

els.tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    els.tabs.forEach((item) => item.classList.remove("active"));
    tab.classList.add("active");
    state.filter = tab.dataset.filter;
    render();
  });
});

els.candidateList.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-decision]");
  if (!button) return;
  setDecision(button.dataset.id, button.dataset.decision);
});

checkApi();
analyzeNote();
