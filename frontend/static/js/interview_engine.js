/**
 * Interview Engine for IMAIRA FairScore.
 * Manages conversational AI multi-turn interview flow, stage transitions,
 * text-to-speech output (TTS) with avatar animation synchronization,
 * and Stage 2 glossary verification integration.
 */

class InterviewEngine {
  constructor(apiBaseUrl = "") {
    this.apiBase = apiBaseUrl;
    this.session = null;
    this.currentQuestion = null;
    this.conversationHistory = [];
    this.isAiSpeaking = false;
    this.isEvaluating = false;
    this.activeVoice = null;

    this.onAiUtteranceCallback = null;
    this.onStageChangeCallback = null;
    this.onEvaluationReadyCallback = null;

    this.initTtsVoices();
  }

  initTtsVoices() {
    if ("speechSynthesis" in window) {
      const loadVoices = () => {
        const voices = window.speechSynthesis.getVoices();
        // Prefer natural English voices
        this.activeVoice = voices.find(v => v.lang.startsWith("en") && (v.name.includes("Natural") || v.name.includes("Google") || v.name.includes("Samantha"))) || voices.find(v => v.lang.startsWith("en")) || voices[0];
      };
      loadVoices();
      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = loadVoices;
      }
    }
  }

  speak(text, onComplete) {
    if (!("speechSynthesis" in window)) {
      if (onComplete) onComplete();
      return;
    }

    window.speechSynthesis.cancel(); // Stop any pending speech
    this.isAiSpeaking = true;

    const utterance = new SpeechSynthesisUtterance(text);
    if (this.activeVoice) utterance.voice = this.activeVoice;
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onend = () => {
      this.isAiSpeaking = false;
      if (onComplete) onComplete();
    };

    utterance.onerror = (e) => {
      console.warn("[InterviewEngine] TTS error:", e);
      this.isAiSpeaking = false;
      if (onComplete) onComplete();
    };

    window.speechSynthesis.speak(utterance);
  }

  stopSpeaking() {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      this.isAiSpeaking = false;
    }
  }

  async startInterview({ candidateName, domain, difficulty, numQuestions }) {
    try {
      const res = await fetch(`${this.apiBase}/interview/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_name: candidateName,
          domain: domain,
          difficulty: difficulty,
          num_questions: parseInt(numQuestions, 10) || 3
        })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to start interview`);
      const data = await res.json();

      this.session = {
        sessionId: data.session_id,
        candidateName: candidateName,
        domain: domain,
        difficulty: difficulty,
        stage: data.stage,
        totalQuestions: data.questions_count,
        questionIndex: 0
      };

      this.currentQuestion = data.first_question;
      this.conversationHistory = [
        { speaker: "interviewer", text: data.greeting, timestamp: new Date() }
      ];

      return {
        success: true,
        greeting: data.greeting,
        firstQuestion: this.currentQuestion,
        session: this.session
      };
    } catch (err) {
      console.error("[InterviewEngine] Error starting session:", err);
      return { success: false, error: err.message };
    }
  }

  async submitCandidateUtterance(candidateUtterance) {
    if (!this.session) return null;

    // 1. Stage 2: Acoustic Verification & Technical Glossary Check
    let verifiedText = candidateUtterance;
    let auditLog = [];

    try {
      const verifyRes = await fetch(`${this.apiBase}/asr/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_transcript: candidateUtterance })
      });

      if (verifyRes.ok) {
        const verifyData = await verifyRes.json();
        verifiedText = verifyData.verified_transcript || candidateUtterance;
        auditLog = verifyData.audit_log || [];
      }
    } catch (e) {
      console.warn("[InterviewEngine] ASR verify non-critical warning:", e);
    }

    // Add candidate utterance to local history
    this.conversationHistory.push({
      speaker: "candidate",
      text: verifiedText,
      originalText: candidateUtterance,
      auditLog: auditLog,
      timestamp: new Date()
    });

    // 2. Submit to conversational AI state engine
    try {
      const turnRes = await fetch(`${this.apiBase}/interview/turn`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: this.session.sessionId,
          candidate_utterance: verifiedText
        })
      });

      if (!turnRes.ok) throw new Error(`HTTP ${turnRes.status}: Turn failed`);
      const turnData = await turnRes.json();

      this.session.stage = turnData.stage;
      if (turnData.current_question_detail) {
        this.currentQuestion = turnData.current_question_detail;
      }

      this.conversationHistory.push({
        speaker: "interviewer",
        text: turnData.ai_response,
        injectionDetected: turnData.injection_detected || false,
        timestamp: new Date()
      });

      // Check if interview concluded
      const isConcluded = turnData.stage === "CONCLUSION";

      return {
        aiResponse: turnData.ai_response,
        stage: turnData.stage,
        currentQuestion: this.currentQuestion,
        verifiedText: verifiedText,
        auditLog: auditLog,
        injectionDetected: turnData.injection_detected,
        isConcluded: isConcluded
      };
    } catch (err) {
      console.error("[InterviewEngine] Error processing turn:", err);
      return {
        aiResponse: "Understood. Let us proceed with the next technical question.",
        stage: this.session.stage,
        currentQuestion: this.currentQuestion,
        verifiedText: verifiedText,
        error: err.message
      };
    }
  }

  async generateFinalEvaluation() {
    if (!this.session) return null;
    this.isEvaluating = true;

    // Collect all candidate answers
    const candidateUtterances = this.conversationHistory
      .filter(m => m.speaker === "candidate")
      .map(m => m.text)
      .join(" ");

    const qText = this.currentQuestion ? this.currentQuestion.question : "Explain technical architecture and system tradeoffs.";
    const qId = this.currentQuestion ? this.currentQuestion.id : "ENG001";

    try {
      const scoreRes = await fetch(`${this.apiBase}/score`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: this.session.sessionId,
          question_id: qId,
          question_text: qText,
          transcript: [
            {
              start: 0.0,
              end: 60.0,
              speaker: "candidate",
              text: candidateUtterances || "Candidate provided full technical discussion."
            }
          ]
        })
      });

      if (!scoreRes.ok) throw new Error(`HTTP ${scoreRes.status}: Scoring failed`);
      const scoreData = await scoreRes.json();
      this.isEvaluating = false;

      return scoreData;
    } catch (err) {
      console.error("[InterviewEngine] Error generating evaluation:", err);
      this.isEvaluating = false;
      return null;
    }
  }
}

window.InterviewEngine = InterviewEngine;
