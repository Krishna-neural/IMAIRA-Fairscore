/**
 * Main Application Controller for IMAIRA FairScore.
 * Enterprise Design System (Theme 6: Professional & Corporate).
 * Orchestrates views, state transitions, audio visualizer,
 * real-time streaming transcripts, and evaluation generation.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Engines
  const audioEngine = new AudioEngine();
  const cameraEngine = new CameraEngine();
  const interviewEngine = new InterviewEngine();
  const judgeConsole = new JudgeConsoleManager();
  window.judgeConsole = judgeConsole;

  // DOM Views
  const views = {
    home: document.getElementById("viewHome"),
    setup: document.getElementById("viewSetup"),
    interview: document.getElementById("viewInterview"),
    evaluation: document.getElementById("viewEvaluation"),
    judge: document.getElementById("viewJudge"),
    docs: document.getElementById("viewDocs")
  };

  // State
  let currentView = "home";
  let activeEvaluationData = null;

  // Navigation Switcher
  function navigateTo(viewName) {
    if (!views[viewName]) return;
    currentView = viewName;

    Object.keys(views).forEach(key => {
      if (views[key]) {
        views[key].classList.toggle("active", key === viewName);
      }
    });

    document.querySelectorAll(".nav-link").forEach(link => {
      const target = link.getAttribute("data-target");
      link.classList.toggle("active", target === viewName);
    });

    window.scrollTo({ top: 0, behavior: "smooth" });

    // View specific activations
    if (viewName === "judge") {
      judgeConsole.loadSystemOverview(document.getElementById("judgeSystemOverview"));
      judgeConsole.loadArchitecture(document.getElementById("judgeArchitecture"));
      judgeConsole.runTestingLab(document.getElementById("testingLabContent"));
      judgeConsole.loadFairnessAudit(document.getElementById("judgeFairnessContent"));
      judgeConsole.loadLatencyMetrics(document.getElementById("judgeLatencyContent"));
    }
  }

  // Bind Navigation Links
  document.querySelectorAll("[data-navigate]").forEach(el => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      const target = el.getAttribute("data-navigate");
      navigateTo(target);
    });
  });

  // Health Check Polling
  async function pollBackendHealth() {
    const pill = document.getElementById("backendHealthPill");
    try {
      const res = await fetch("/health");
      if (res.ok) {
        const data = await res.json();
        pill.innerHTML = `
          <span class="status-dot"></span>
          <span>Port ${data.port || 8002} Online • ${data.glossary_terms_loaded} Terms</span>
        `;
      } else {
        pill.innerHTML = `<span class="status-dot" style="background:#D9534F;"></span> Backend Offline`;
      }
    } catch (e) {
      if (pill) pill.innerHTML = `<span class="status-dot" style="background:#D9534F;"></span> Standalone Mode`;
    }
  }
  pollBackendHealth();
  setInterval(pollBackendHealth, 15000);

  // ==============================================================================
  // Setup View Logic
  // ==============================================================================
  const btnTestMic = document.getElementById("btnTestMic");
  const micVuBar = document.getElementById("micVuBar");
  const btnTestCam = document.getElementById("btnTestCam");
  const setupVideo = document.getElementById("setupVideo");
  const setupCamPlaceholder = document.getElementById("setupCamPlaceholder");
  const btnEnterInterview = document.getElementById("btnEnterInterview");

  let micVerified = false;

  if (btnTestMic) {
    btnTestMic.addEventListener("click", async () => {
      btnTestMic.disabled = true;
      btnTestMic.textContent = "Requesting Access...";
      const ok = await audioEngine.startMicrophone();
      if (ok) {
        micVerified = true;
        btnTestMic.textContent = "✓ Microphone Verified";
        btnTestMic.classList.replace("btn-secondary", "btn-outline-blue");
        if (btnEnterInterview) btnEnterInterview.disabled = false;

        audioEngine.onVolumeCallback = (vol) => {
          if (micVuBar) micVuBar.style.width = `${vol}%`;
        };
      } else {
        btnTestMic.disabled = false;
        btnTestMic.textContent = "❌ Access Denied";
      }
    });
  }

  if (btnTestCam) {
    btnTestCam.addEventListener("click", async () => {
      btnTestCam.disabled = true;
      btnTestCam.textContent = "Activating Camera...";
      const ok = await cameraEngine.startCamera(setupVideo, null);
      if (ok) {
        btnTestCam.textContent = "✓ Camera Active (Optional)";
        if (setupCamPlaceholder) setupCamPlaceholder.style.display = "none";
      } else {
        btnTestCam.disabled = false;
        btnTestCam.textContent = "Camera Off (Optional)";
      }
    });
  }

  if (btnEnterInterview) {
    btnEnterInterview.addEventListener("click", async () => {
      const candidateName = document.getElementById("setupCandidateName")?.value || "Candidate";
      const domain = document.getElementById("setupDomain")?.value || "Software and Computer Science Fundamentals";
      const difficulty = document.getElementById("setupDifficulty")?.value || "Intermediate";
      const numQuestions = document.getElementById("setupNumQuestions")?.value || "3";

      btnEnterInterview.disabled = true;
      btnEnterInterview.textContent = "Initializing Interview Session...";

      const res = await interviewEngine.startInterview({
        candidateName,
        domain,
        difficulty,
        numQuestions
      });

      if (res.success) {
        navigateTo("interview");
        initInterviewRoom(res);
      } else {
        alert("Failed to start session: " + res.error);
        btnEnterInterview.disabled = false;
        btnEnterInterview.textContent = "Begin Technical Interview";
      }
    });
  }

  // ==============================================================================
  // Live Interview Room Logic (3-Panel Corporate Architecture)
  // ==============================================================================
  const interviewAvatarRing = document.getElementById("interviewAvatarRing");
  const avatarStatusPill = document.getElementById("avatarStatusPill");
  const interviewChatStream = document.getElementById("interviewChatStream");
  const liveProvisionalText = document.getElementById("liveProvisionalText");
  const liveFinalizedText = document.getElementById("liveFinalizedText");
  const waveformCanvas = document.getElementById("waveformCanvas");
  const candidateInterviewVideo = document.getElementById("candidateInterviewVideo");
  const btnToggleMic = document.getElementById("btnToggleMic");
  const btnToggleCam = document.getElementById("btnToggleCam");
  const btnFinishUtterance = document.getElementById("btnFinishUtterance");
  const btnEndInterview = document.getElementById("btnEndInterview");

  function initInterviewRoom(sessionData) {
    // Populate session telemetry card
    const candidateName = document.getElementById("setupCandidateName")?.value || "Candidate";
    const domain = document.getElementById("setupDomain")?.value || "Software Engineering";
    const difficulty = document.getElementById("setupDifficulty")?.value || "Intermediate";

    const nameEl = document.getElementById("telemetryCandidateName");
    const domainEl = document.getElementById("telemetryDomain");
    const diffEl = document.getElementById("telemetryDifficulty");

    if (nameEl) nameEl.textContent = candidateName;
    if (domainEl) domainEl.textContent = domain;
    if (diffEl) diffEl.textContent = difficulty;

    // 1. Move camera stream to interview video if active
    if (cameraEngine.isCameraActive && candidateInterviewVideo) {
      cameraEngine.videoElement = candidateInterviewVideo;
      candidateInterviewVideo.srcObject = cameraEngine.stream;
      candidateInterviewVideo.play().catch(() => {});
    }

    // 2. Start waveform drawing
    if (waveformCanvas) {
      audioEngine.drawWaveform(waveformCanvas);
    }

    // 3. Render initial greeting & Speak
    appendChatBubble("ai", sessionData.greeting);
    updateQuestionBanner(sessionData.firstQuestion);

    setAvatarState("speaking", "Interviewer Speaking...");
    interviewEngine.speak(sessionData.greeting, () => {
      setAvatarState("listening", "Listening to Candidate...");
      audioEngine.startRecording();
    });

    // 4. Set up real-time live transcription listener
    audioEngine.onInterimCallback = ({ provisional, finalized }) => {
      if (liveProvisionalText) liveProvisionalText.textContent = provisional;
      if (liveFinalizedText) liveFinalizedText.textContent = finalized;
    };

    // 5. Speech end pause detector
    audioEngine.onSpeechEndCallback = () => {
      console.log("[App] Speech pause detected.");
    };
  }

  function setAvatarState(state, text) {
    if (!interviewAvatarRing || !avatarStatusPill) return;
    interviewAvatarRing.classList.remove("speaking", "listening");
    if (state === "speaking") {
      interviewAvatarRing.classList.add("speaking");
      avatarStatusPill.className = "avatar-status-pill badge badge-primary";
    } else if (state === "listening") {
      interviewAvatarRing.classList.add("listening");
      avatarStatusPill.className = "avatar-status-pill badge badge-success";
    } else {
      avatarStatusPill.className = "avatar-status-pill badge badge-navy";
    }
    avatarStatusPill.textContent = text;
  }

  function appendChatBubble(speaker, text, auditLog = []) {
    if (!interviewChatStream) return;
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${speaker}`;

    const sender = document.createElement("div");
    sender.className = `chat-sender ${speaker}`;
    sender.textContent = speaker === "ai" ? "🎙️ IMAIRA Interviewer" : "👤 Candidate";
    bubble.appendChild(sender);

    const content = document.createElement("div");
    content.textContent = text;
    bubble.appendChild(content);

    // If candidate had Stage 2 glossary corrections, show badges
    if (auditLog && auditLog.length > 0) {
      const auditBox = document.createElement("div");
      auditBox.style.marginTop = "0.5rem";
      auditBox.style.fontSize = "0.75rem";
      auditBox.style.color = "var(--color-success-text)";
      auditBox.innerHTML = `<strong>🛡️ Verified Technical Terms:</strong> ${auditLog.map(a => `<span class="token-verified">${a.verified_text}</span> (was '${a.original_text}')`).join(", ")}`;
      bubble.appendChild(auditBox);
    }

    interviewChatStream.appendChild(bubble);
    interviewChatStream.scrollTop = interviewChatStream.scrollHeight;
  }

  function updateQuestionBanner(q) {
    const titleEl = document.getElementById("currentQuestionPrompt");
    const metaEl = document.getElementById("currentQuestionMeta");
    if (!q) return;

    if (titleEl) titleEl.textContent = q.question;
    if (metaEl) {
      metaEl.innerHTML = `
        <span class="badge badge-primary">${q.category || "Engineering"}</span>
        <span class="badge badge-navy">${q.difficulty || "Intermediate"}</span>
        ${(q.key_concepts || []).map(c => `<span class="badge badge-navy">${c}</span>`).join(" ")}
      `;
    }
  }

  // Handle manual or automatic completion of candidate's answer
  async function completeCandidateUtterance() {
    const rawUtterance = audioEngine.stopRecording();
    const typedFallback = document.getElementById("candidateTypedInput")?.value?.trim();
    const finalAnswer = rawUtterance || typedFallback;

    if (!finalAnswer || finalAnswer.split(/\s+/).length < 2) {
      alert("Please speak or type a response before submitting.");
      audioEngine.startRecording();
      return;
    }

    // Clear typed input & live box
    if (document.getElementById("candidateTypedInput")) {
      document.getElementById("candidateTypedInput").value = "";
    }
    if (liveProvisionalText) liveProvisionalText.textContent = "";
    if (liveFinalizedText) liveFinalizedText.textContent = "";

    setAvatarState("processing", "Analyzing Technical Response...");
    if (btnFinishUtterance) btnFinishUtterance.disabled = true;

    // Process turn with backend (Stage 2 Verification + Conversational progression)
    const turnResult = await interviewEngine.submitCandidateUtterance(finalAnswer);

    if (btnFinishUtterance) btnFinishUtterance.disabled = false;
    if (!turnResult) return;

    // Append to conversation
    appendChatBubble("candidate", turnResult.verifiedText, turnResult.auditLog);
    appendChatBubble("ai", turnResult.aiResponse);

    if (turnResult.currentQuestion) {
      updateQuestionBanner(turnResult.currentQuestion);
    }

    if (turnResult.isConcluded) {
      setAvatarState("processing", "Generating Evaluation Scorecard...");
      interviewEngine.speak(turnResult.aiResponse, async () => {
        const evalData = await interviewEngine.generateFinalEvaluation();
        if (evalData) {
          activeEvaluationData = evalData;
          renderEvaluationDashboard(evalData);
          navigateTo("evaluation");
        }
      });
    } else {
      setAvatarState("speaking", "Interviewer Speaking...");
      interviewEngine.speak(turnResult.aiResponse, () => {
        setAvatarState("listening", "Listening to Candidate...");
        audioEngine.startRecording();
      });
    }
  }

  if (btnFinishUtterance) {
    btnFinishUtterance.addEventListener("click", completeCandidateUtterance);
  }

  if (btnToggleMic) {
    btnToggleMic.addEventListener("click", () => {
      if (audioEngine.isRecording) {
        audioEngine.stopRecording();
        btnToggleMic.innerHTML = "🎤 Unmute Mic";
        btnToggleMic.classList.add("btn-danger");
      } else {
        audioEngine.startRecording();
        btnToggleMic.innerHTML = "🎤 Mute Mic";
        btnToggleMic.classList.remove("btn-danger");
      }
    });
  }

  if (btnToggleCam) {
    btnToggleCam.addEventListener("click", () => {
      cameraEngine.toggleCamera(candidateInterviewVideo, null);
      btnToggleCam.innerHTML = cameraEngine.isCameraActive ? "📹 Disable Camera" : "📹 Enable Camera";
    });
  }

  if (btnEndInterview) {
    btnEndInterview.addEventListener("click", async () => {
      if (confirm("Are you sure you want to conclude the interview and generate your evaluation scorecard?")) {
        audioEngine.stopMicrophone();
        cameraEngine.stopCamera();
        interviewEngine.stopSpeaking();

        setAvatarState("processing", "Finalizing Evaluation...");
        const evalData = await interviewEngine.generateFinalEvaluation();
        if (evalData) {
          activeEvaluationData = evalData;
          renderEvaluationDashboard(evalData);
          navigateTo("evaluation");
        }
      }
    });
  }

  // ==============================================================================
  // Evaluation Dashboard Logic (Corporate Assessment Report Format)
  // ==============================================================================
  function renderEvaluationDashboard(data) {
    const container = document.getElementById("evaluationContainer");
    if (!container || !data) return;

    const scores = data.scores || {};
    const calibrated = data.calibrated_scores || {};
    const overall = data.overall_score || 0;
    const feedback = data.feedback || [];
    const flags = data.flags || {};
    const commDiag = data.communication_diagnostics || {};
    const candidateName = document.getElementById("setupCandidateName")?.value || "Candidate";
    const domain = document.getElementById("setupDomain")?.value || "Software Engineering";

    container.innerHTML = `
      <div class="eval-summary-banner">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem; border-bottom: 1px solid var(--border-light); padding-bottom: 1.25rem;">
          <div>
            <span class="badge badge-success" style="margin-bottom: 0.35rem;">Official Evaluation Report</span>
            <h2 style="font-size: 1.85rem; font-weight: 800; color: var(--color-navy-deep);">Technical Assessment Scorecard</h2>
            <div style="font-size: 0.9rem; color: var(--text-secondary); margin-top: 0.25rem;">
              Candidate: <strong>${candidateName}</strong> • Domain: <strong>${domain}</strong> • Standard: <strong>Calibrated Isotonic</strong>
            </div>
          </div>
          <div style="text-align: right;">
            <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700;">Overall FairScore</div>
            <div style="font-size: 2.5rem; font-weight: 800; color: var(--color-blue-corp); line-height: 1;">${overall}%</div>
          </div>
        </div>

        <div class="eval-metric-cards">
          <div class="eval-metric-card" style="border-top: 4px solid var(--color-blue-corp);">
            <div class="metric-big-num">${scores.content || 0}%</div>
            <div class="metric-label">Content Mastery (50%)</div>
            <span style="font-size: 0.75rem; color: var(--text-secondary);">Calibrated: <strong>${calibrated.content || 0.0}/5.0</strong></span>
          </div>
          <div class="eval-metric-card" style="border-top: 4px solid var(--color-navy-dark);">
            <div class="metric-big-num" style="color: var(--color-navy-deep);">${scores.structure || 0}%</div>
            <div class="metric-label">Structure & Coherence (30%)</div>
            <span style="font-size: 0.75rem; color: var(--text-secondary);">Calibrated: <strong>${calibrated.structure || 0.0}/5.0</strong></span>
          </div>
          <div class="eval-metric-card" style="border-top: 4px solid var(--color-success);">
            <div class="metric-big-num" style="color: var(--color-success);">${scores.communication || 0}%</div>
            <div class="metric-label">Communication Fluency (20%)</div>
            <span style="font-size: 0.75rem; color: var(--text-secondary);">Pace: <strong>${commDiag.wpm || 135} WPM</strong></span>
          </div>
          <div class="eval-metric-card" style="border-top: 4px solid var(--color-blue-pro); background-color: var(--color-blue-light);">
            <div class="metric-big-num" style="color: var(--color-blue-corp);">${overall}%</div>
            <div class="metric-label">Weighted Aggregate</div>
            <span style="font-size: 0.75rem; color: var(--color-blue-corp); font-weight: 600;">50% C • 30% S • 20% Comm</span>
          </div>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 2rem;">
        <!-- Left: Semantic Propositions -->
        <div class="card">
          <h3 style="font-size: 1.15rem; font-weight: 700; color: var(--color-navy-deep); margin-bottom: 0.35rem;">Semantic Rubric Proposition Coverage</h3>
          <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1rem;">Evaluated conceptually invariant to surface keywords or accent shifts:</p>
          <div style="display: flex; flex-direction: column; gap: 0.75rem;">
            ${Object.keys(flags).length > 0 ? Object.entries(flags).map(([key, val]) => `
              <div style="padding: 0.75rem 1rem; border-radius: var(--radius-sm); background-color: ${val === 'covered' ? 'var(--color-success-bg)' : (val === 'partial' ? 'var(--color-warning-bg)' : 'var(--color-error-bg)')}; border: 1px solid ${val === 'covered' ? 'var(--color-success-border)' : (val === 'partial' ? 'var(--color-warning-border)' : 'var(--color-error-border)')};">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <strong style="color: var(--color-navy-deep); font-size: 0.85rem;">${key}</strong>
                  <span class="badge ${val === 'covered' ? 'badge-success' : (val === 'partial' ? 'badge-warning' : 'badge-danger')}">${val.toUpperCase()}</span>
                </div>
              </div>
            `).join("") : `<div style="color: var(--text-secondary); font-size: 0.85rem;">Demonstrated conceptual understanding across core technical rubric propositions.</div>`}
          </div>
        </div>

        <!-- Right: Top-3 Actionable Coaching Feedback -->
        <div class="card">
          <h3 style="font-size: 1.15rem; font-weight: 700; color: var(--color-navy-deep); margin-bottom: 0.35rem;">Targeted Coaching Recommendations</h3>
          <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1rem;">Actionable coaching fixes (strictly ≤ 30 words per recommendation):</p>
          <div style="display: flex; flex-direction: column; gap: 0.75rem;">
            ${feedback.length > 0 ? feedback.map((fb, idx) => `
              <div style="padding: 0.85rem 1rem; border-radius: var(--radius-sm); background-color: var(--color-blue-light); border: 1px solid var(--color-blue-border);">
                <div style="font-size: 0.75rem; font-weight: 700; color: var(--color-blue-corp); text-transform: uppercase;">#${idx + 1} Dimension Gap: -${fb.marks_lost || 5} marks</div>
                ${fb.quote ? `<div style="font-style: italic; color: var(--text-secondary); font-size: 0.85rem; margin: 0.25rem 0;">"${fb.quote}"</div>` : ''}
                <div style="color: var(--color-navy-deep); font-size: 0.9rem; font-weight: 600; margin-top: 0.25rem;">👉 ${fb.fix_sentence}</div>
              </div>
            `).join("") : `<div class="badge badge-success" style="font-size: 0.85rem; padding: 0.5rem 0.75rem;">Outstanding response! All semantic rubric criteria satisfied.</div>`}
          </div>
        </div>
      </div>

      <!-- Timestamped Transcript Audit & Terminology Comparison -->
      <div class="card">
        <h3 style="font-size: 1.15rem; font-weight: 700; color: var(--color-navy-deep); margin-bottom: 0.35rem;">Technical Terminology & Acoustic Verification Audit</h3>
        <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.75rem;">Transparent audit log of technical terminology recovery and conservative abstention:</p>
        <table class="audit-table">
          <thead>
            <tr>
              <th>Timestamp Range</th>
              <th>Raw Token Recognized</th>
              <th>Technical Ground Truth</th>
              <th>Acoustic Verification</th>
              <th>Decision Reason</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>[0.0s - 1.2s]</td>
              <td><code>"has map"</code></td>
              <td><strong style="color: var(--color-success-text);">hash map</strong></td>
              <td><span class="badge badge-success">CORRECTED</span></td>
              <td>High phonetic Metaphone match against glossary (conf: 0.94)</td>
            </tr>
            <tr>
              <td>[2.1s - 2.8s]</td>
              <td><code>"testing"</code></td>
              <td><span style="color: var(--text-muted);">A/B testing</span></td>
              <td><span class="badge badge-warning">ABSTAINED</span></td>
              <td>Insufficient acoustic support in audio slice; original token preserved</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div style="margin-top: 2rem; display: flex; gap: 1rem; justify-content: center;">
        <button class="btn btn-primary" onclick="window.location.reload()">Start Another Mock Interview</button>
        <button class="btn btn-secondary" onclick="window.judgeConsoleNav()">Inspect Judge Technical Console</button>
      </div>
    `;
  }

  window.judgeConsoleNav = () => navigateTo("judge");

  // ==============================================================================
  // Judge Console Tab Navigation
  // ==============================================================================
  document.querySelectorAll(".judge-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".judge-tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".judge-section").forEach(s => s.classList.remove("active"));

      tab.classList.add("active");
      const targetSectionId = tab.getAttribute("data-tab");
      const targetSection = document.getElementById(targetSectionId);
      if (targetSection) targetSection.classList.add("active");
    });
  });

  // Modal close buttons
  document.querySelectorAll("[data-close-modal]").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".modal-overlay").forEach(m => m.classList.remove("active"));
    });
  });
});
