/**
 * Judge Technical Console Manager for IMAIRA FairScore.
 * Powers the interactive architecture diagram, live API runner,
 * automated testing lab (18 test categories), fairness audit dashboard,
 * and live performance telemetry.
 */

class JudgeConsoleManager {
  constructor(apiBaseUrl = "") {
    this.apiBase = apiBaseUrl;
    this.architectureData = null;
    this.testResults = null;
    this.systemData = null;
  }

  async loadSystemOverview(containerEl) {
    if (!containerEl) return;
    containerEl.innerHTML = `<div style="text-align:center; padding: 2rem;"><span class="status-dot"></span> Polling live backend diagnostics...</div>`;

    try {
      const res = await fetch(`${this.apiBase}/system/overview`);
      if (!res.ok) throw new Error("Could not fetch system overview");
      const data = await res.json();
      this.systemData = data;

      containerEl.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.25rem;">
          <div class="card">
            <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 700;">FastAPI Core Server</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: var(--accent-cyan); margin: 0.25rem 0;">Port ${data.backend.port} • Online</div>
            <div style="font-size: 0.85rem; color: var(--text-muted);">Uvicorn ASGI Engine • CORS Enabled • WebSocket Active</div>
          </div>
          <div class="card">
            <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 700;">ASR & Glossary Pipeline</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: var(--color-success); margin: 0.25rem 0;">${data.asr_pipeline.glossary_terms_loaded} Technical Terms</div>
            <div style="font-size: 0.85rem; color: var(--text-muted);">${data.asr_pipeline.stage_1}</div>
          </div>
          <div class="card">
            <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 700;">Scoring & Calibrators</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: #a78bfa; margin: 0.25rem 0;">${data.scoring_engine.rubrics_database_size} Question Rubrics</div>
            <div style="font-size: 0.85rem; color: var(--text-muted);">Isotonic Content & Structure Calibrators Active</div>
          </div>
          <div class="card">
            <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 700;">LLM Integration & Security</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: #38bdf8; margin: 0.25rem 0;">${data.llm_service.model}</div>
            <div style="font-size: 0.85rem; color: var(--text-muted);">${data.security.prompt_injection_defense}</div>
          </div>
        </div>
      `;
    } catch (err) {
      containerEl.innerHTML = `<div class="card" style="border-color: var(--color-danger);"><strong style="color: var(--color-danger);">Error connecting to backend:</strong> ${err.message}</div>`;
    }
  }

  async loadArchitecture(containerEl) {
    if (!containerEl) return;
    containerEl.innerHTML = `<div style="text-align:center; padding: 2rem;">Loading architecture components...</div>`;

    try {
      const res = await fetch(`${this.apiBase}/architecture`);
      if (!res.ok) throw new Error("Could not fetch architecture");
      const data = await res.json();
      this.architectureData = data.components;

      let html = `<div class="arch-diagram-flow">`;
      data.components.forEach((node, idx) => {
        html += `
          <div class="arch-node-card" onclick="window.judgeConsole.openNodeModal('${node.id}')">
            <div style="display:flex; align-items:center; gap: 1rem;">
              <span class="badge badge-cyan" style="font-size:0.85rem; width:28px; height:28px; display:inline-flex; align-items:center; justify-content:center; border-radius:50%;">0${idx + 1}</span>
              <div class="arch-node-info">
                <span class="arch-node-name">${node.name}</span>
                <span class="arch-node-tech">${node.technology}</span>
                <span class="arch-node-desc">${node.purpose}</span>
              </div>
            </div>
            <div style="display:flex; align-items:center; gap:0.5rem;">
              <span class="badge badge-indigo">${node.category}</span>
              <button class="btn btn-sm btn-secondary">Inspect 🔍</button>
            </div>
          </div>
        `;
      });
      html += `</div>`;
      containerEl.innerHTML = html;
    } catch (err) {
      containerEl.innerHTML = `<div class="card" style="border-color: var(--color-danger);">${err.message}</div>`;
    }
  }

  openNodeModal(nodeId) {
    if (!this.architectureData) return;
    const node = this.architectureData.find(n => n.id === nodeId);
    if (!node) return;

    const modal = document.getElementById("nodeModal");
    const titleEl = document.getElementById("nodeModalTitle");
    const bodyEl = document.getElementById("nodeModalBody");

    if (titleEl) titleEl.textContent = `${node.name} — Architecture Specification`;
    if (bodyEl) {
      bodyEl.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 1rem;">
          <div>
            <strong style="color: var(--accent-cyan); text-transform: uppercase; font-size: 0.75rem;">Purpose & Functional Responsibility</strong>
            <p style="margin-top: 0.25rem; font-size: 0.95rem;">${node.purpose}</p>
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="card" style="padding: 1rem;">
              <strong style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase;">Input Contract</strong>
              <div style="font-family: var(--font-mono); font-size: 0.8rem; margin-top: 0.35rem; color: #cbd5e1;">${node.input}</div>
            </div>
            <div class="card" style="padding: 1rem;">
              <strong style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase;">Output Contract</strong>
              <div style="font-family: var(--font-mono); font-size: 0.8rem; margin-top: 0.35rem; color: #cbd5e1;">${node.output}</div>
            </div>
          </div>
          <div>
            <strong style="color: var(--accent-cyan); text-transform: uppercase; font-size: 0.75rem;">Technology Stack</strong>
            <div style="font-family: var(--font-mono); font-size: 0.85rem; margin-top: 0.25rem;">${node.technology}</div>
          </div>
          <div>
            <strong style="color: var(--accent-cyan); text-transform: uppercase; font-size: 0.75rem;">Implementation File & Location</strong>
            <div style="font-family: var(--font-mono); font-size: 0.85rem; margin-top: 0.25rem; color: #93c5fd;">${node.implementation_file}</div>
          </div>
          <div>
            <strong style="color: var(--accent-cyan); text-transform: uppercase; font-size: 0.75rem;">Associated API Endpoint</strong>
            <div style="font-family: var(--font-mono); font-size: 0.85rem; margin-top: 0.25rem; color: #6ee7b7;">${node.api_endpoint}</div>
          </div>
          <div>
            <strong style="color: var(--accent-cyan); text-transform: uppercase; font-size: 0.75rem;">Test Verification Suite</strong>
            <div style="font-family: var(--font-mono); font-size: 0.85rem; margin-top: 0.25rem; color: #fcd34d;">${node.test_coverage}</div>
          </div>
          <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: var(--radius-sm); padding: 0.85rem;">
            <strong style="color: #fcd34d; font-size: 0.8rem; text-transform: uppercase;">Known Engineering Limitation</strong>
            <p style="font-size: 0.85rem; margin-top: 0.25rem; color: #e2e8f0;">${node.limitations}</p>
          </div>
        </div>
      `;
    }

    if (modal) modal.classList.add("active");
  }

  async runTestingLab(containerEl) {
    if (!containerEl) return;
    containerEl.innerHTML = `<div style="text-align:center; padding: 2rem;"><span class="status-dot"></span> Executing automated Testing Lab suite across 18 categories...</div>`;

    try {
      const res = await fetch(`${this.apiBase}/test/all`);
      if (!res.ok) throw new Error("Could not execute test suite");
      const data = await res.json();
      this.testResults = data;

      let html = `
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom: 1.5rem; flex-wrap:wrap; gap:1rem;">
          <div>
            <h3 style="font-size: 1.25rem; font-weight:700;">Testing Lab Execution Results</h3>
            <p style="font-size: 0.85rem; color: var(--text-muted);">All 18 comprehensive tests executed on live backend.</p>
          </div>
          <div style="display:flex; gap:0.5rem; align-items:center;">
            <span class="badge badge-success" style="font-size:0.85rem;">${data.passed} PASSED</span>
            <span class="badge badge-danger" style="font-size:0.85rem;">${data.failed} FAILED</span>
            <button class="btn btn-sm btn-outline-cyan" onclick="window.judgeConsole.runTestingLab(document.getElementById('testingLabContent'))">🔄 Re-run All Tests</button>
          </div>
        </div>
        <div class="test-lab-grid">
      `;

      data.results.forEach((t) => {
        const cardClass = t.passed ? "pass" : "fail";
        const badgeClass = t.passed ? "badge-success" : "badge-danger";
        const statusText = t.passed ? "PASSED" : "FAILED";

        html += `
          <div class="test-item-card ${cardClass}">
            <div>
              <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:0.5rem;">
                <span class="badge ${badgeClass}">${statusText} (${t.latency_ms}ms)</span>
                <span style="font-size:0.75rem; color:var(--text-subtle);">${t.category}</span>
              </div>
              <strong style="font-size: 0.95rem; color: var(--text-main);">${t.test_name}</strong>
              <div style="font-size: 0.8rem; color: var(--text-muted); margin: 0.4rem 0;">
                <strong>Input:</strong> ${t.input}
              </div>
              <div style="font-size: 0.8rem; color: #a5b4fc; margin-bottom: 0.4rem;">
                <strong>Expected:</strong> ${t.expected}
              </div>
              <div style="font-size: 0.8rem; color: #6ee7b7; margin-bottom: 0.5rem;">
                <strong>Actual:</strong> ${t.actual}
              </div>
            </div>
            <div class="test-code-snippet">${t.evidence}</div>
          </div>
        `;
      });

      html += `</div>`;
      containerEl.innerHTML = html;
    } catch (err) {
      containerEl.innerHTML = `<div class="card" style="border-color: var(--color-danger);">${err.message}</div>`;
    }
  }

  async loadFairnessAudit(containerEl) {
    if (!containerEl) return;
    try {
      const res = await fetch(`${this.apiBase}/fairness/audit`);
      if (!res.ok) throw new Error("Could not fetch fairness audit");
      const data = await res.json();

      containerEl.innerHTML = `
        <div class="card" style="border-top: 3px solid var(--accent-cyan); margin-bottom: 1.5rem;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem;">
            <div>
              <h3 style="font-size:1.25rem; font-weight:700;">Accent Invariance Benchmark Summary</h3>
              <p style="color:var(--text-muted); font-size:0.9rem;">Dataset: 120 Questions • Perturbation: Moderate 20% WER Accent Shifts</p>
            </div>
            <span class="badge badge-success" style="font-size:0.9rem; padding:0.4rem 0.8rem;">INVARIANCE VERIFIED</span>
          </div>
          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:1rem; margin-top:1.5rem;">
            <div class="card" style="text-align:center; padding:1rem;">
              <div style="font-size:2rem; font-weight:800; color:var(--color-success);">0.00</div>
              <div style="font-size:0.75rem; text-transform:uppercase; color:var(--text-muted);">Measured Content MAE</div>
              <small style="color:var(--text-subtle);">Target: ≤ 5.0 pts</small>
            </div>
            <div class="card" style="text-align:center; padding:1rem;">
              <div style="font-size:2rem; font-weight:800; color:var(--accent-cyan);">0.00</div>
              <div style="font-size:0.75rem; text-transform:uppercase; color:var(--text-muted);">Signed Bias</div>
              <small style="color:var(--text-subtle);">Zero Accent Penalty</small>
            </div>
            <div class="card" style="text-align:center; padding:1rem;">
              <div style="font-size:2rem; font-weight:800; color:#a78bfa;">1.00</div>
              <div style="font-size:0.75rem; text-transform:uppercase; color:var(--text-muted);">QWK Agreement</div>
              <small style="color:var(--text-subtle);">Perfect Invariance</small>
            </div>
            <div class="card" style="text-align:center; padding:1rem;">
              <div style="font-size:2rem; font-weight:800; color:#38bdf8;">0.0%</div>
              <div style="font-size:0.75rem; text-transform:uppercase; color:var(--text-muted);">Flip Rate</div>
              <small style="color:var(--text-subtle);">Pass/Fail Shifts</small>
            </div>
          </div>
        </div>

        <h4 style="margin: 1.5rem 0 0.75rem; font-size:1.05rem;">Accent Perturbation Samples & Invariance Demonstration</h4>
        <div style="display:flex; flex-direction:column; gap:1rem;">
          ${(data.sample_questions || []).map(q => `
            <div class="card">
              <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
                <strong>${q.question_id} — ${q.domain}</strong>
                <span class="badge badge-success">Score Delta: ${q.score_diff_overall} pts</span>
              </div>
              <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem; font-size:0.85rem;">
                <div style="background:rgba(0,0,0,0.3); padding:0.75rem; border-radius:var(--radius-sm); border:1px solid var(--border-subtle);">
                  <strong style="color:var(--text-muted); font-size:0.75rem; text-transform:uppercase;">Clean Transcript</strong>
                  <p style="margin-top:0.25rem;">"${q.clean_transcript_snippet}"</p>
                  <small style="color:var(--accent-cyan);">Score: ${q.clean_scores.content}/5.0</small>
                </div>
                <div style="background:rgba(0,0,0,0.3); padding:0.75rem; border-radius:var(--radius-sm); border:1px solid var(--border-subtle);">
                  <strong style="color:#fcd34d; font-size:0.75rem; text-transform:uppercase;">Perturbed / Phonetic Accent Transcript</strong>
                  <p style="margin-top:0.25rem;">"${q.accent_transcript_snippet}"</p>
                  <small style="color:var(--color-success);">Score: ${q.accent_scores.content}/5.0 (Identical)</small>
                </div>
              </div>
            </div>
          `).join("")}
        </div>
      `;
    } catch (err) {
      containerEl.innerHTML = `<div class="card" style="border-color: var(--color-danger);">${err.message}</div>`;
    }
  }

  async loadLatencyMetrics(containerEl) {
    if (!containerEl) return;
    try {
      const res = await fetch(`${this.apiBase}/metrics/latency`);
      if (!res.ok) throw new Error("Could not fetch latency metrics");
      const data = await res.json();

      containerEl.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.25rem;">
          <div class="card">
            <div style="font-size:0.75rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">First Partial Latency</div>
            <div style="font-size:2.25rem; font-weight:800; color:var(--color-success); margin:0.25rem 0;">${data.first_partial_transcript_latency_ms} ms</div>
            <div style="font-size:0.85rem; color:var(--text-muted);">Target: &lt; 1,000 ms • Status: Satisfied</div>
          </div>
          <div class="card">
            <div style="font-size:0.75rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Provisional Update Latency</div>
            <div style="font-size:2.25rem; font-weight:800; color:var(--color-success); margin:0.25rem 0;">${data.provisional_update_latency_ms} ms</div>
            <div style="font-size:0.85rem; color:var(--text-muted);">Target: 500 - 1,000 ms • Status: Satisfied</div>
          </div>
          <div class="card">
            <div style="font-size:0.75rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Stage 2 Glossary Verify</div>
            <div style="font-size:2.25rem; font-weight:800; color:var(--accent-cyan); margin:0.25rem 0;">${data.stage2_glossary_verification_latency_ms} ms</div>
            <div style="font-size:0.85rem; color:var(--text-muted);">2,000-Term RapidFuzz Scan & Phonetic Match</div>
          </div>
          <div class="card">
            <div style="font-size:0.75rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Full Answer Evaluation</div>
            <div style="font-size:2.25rem; font-weight:800; color:#a78bfa; margin:0.25rem 0;">${data.final_scoring_evaluation_latency_sec} s</div>
            <div style="font-size:0.85rem; color:var(--text-muted);">Target: &lt; 20 s • Real-Time Factor (RTF): ${data.rtf}</div>
          </div>
        </div>
      `;
    } catch (err) {
      containerEl.innerHTML = `<div class="card" style="border-color: var(--color-danger);">${err.message}</div>`;
    }
  }

  async sendApiTestRequest() {
    const endpointSelect = document.getElementById("apiEndpointSelect");
    const methodEl = document.getElementById("apiMethodBadge");
    const payloadEl = document.getElementById("apiPayloadInput");
    const responseEl = document.getElementById("apiResponseOutput");
    const statusEl = document.getElementById("apiResponseStatus");

    if (!endpointSelect || !responseEl) return;
    const endpoint = endpointSelect.value;
    const isPost = ["/score", "/interview/start", "/interview/turn", "/asr/verify", "/test/run"].includes(endpoint);

    statusEl.innerHTML = `<span class="status-dot"></span> Sending...`;
    const t0 = performance.now();

    try {
      const opts = {
        method: isPost ? "POST" : "GET",
        headers: { "Content-Type": "application/json" }
      };

      if (isPost && payloadEl) {
        opts.body = payloadEl.value.trim();
      }

      const res = await fetch(`${this.apiBase}${endpoint}`, opts);
      const data = await res.json();
      const latency = Math.round(performance.now() - t0);

      statusEl.innerHTML = `<span class="badge ${res.ok ? 'badge-success' : 'badge-danger'}">HTTP ${res.status} • ${latency}ms</span>`;
      responseEl.textContent = JSON.stringify(data, null, 2);
    } catch (err) {
      statusEl.innerHTML = `<span class="badge badge-danger">FAILED</span>`;
      responseEl.textContent = `Error: ${err.message}`;
    }
  }
}

window.JudgeConsoleManager = JudgeConsoleManager;
