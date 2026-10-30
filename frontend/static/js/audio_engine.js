/**
 * Audio Engine for IMAIRA FairScore.
 * Handles microphone capture, Web Audio API AnalyserNode visualizer,
 * Voice Activity Detection (VAD), and real-time streaming speech recognition.
 */

class AudioEngine {
  constructor() {
    this.audioContext = null;
    this.mediaStream = null;
    this.analyser = null;
    this.sourceNode = null;
    this.recognition = null;

    this.isRecording = false;
    this.isSpeaking = false;
    this.volume = 0;
    this.silenceTimer = null;
    this.silenceThresholdMs = 2500; // 2.5s pause before auto-submitting answer

    this.provisionalText = "";
    this.finalizedText = "";
    this.onInterimCallback = null;
    this.onFinalCallback = null;
    this.onVolumeCallback = null;
    this.onSpeechStartCallback = null;
    this.onSpeechEndCallback = null;

    this.initSpeechRecognition();
  }

  initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.lang = "en-US";

      this.recognition.onstart = () => {
        console.log("[AudioEngine] SpeechRecognition active");
      };

      this.recognition.onresult = (event) => {
        let interim = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const transcriptPiece = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            this.finalizedText += (this.finalizedText ? " " : "") + transcriptPiece.trim();
          } else {
            interim += transcriptPiece;
          }
        }
        this.provisionalText = interim;

        // Reset silence detection timer
        this.handleUserVoiceActivity();

        if (this.onInterimCallback) {
          this.onInterimCallback({
            provisional: this.provisionalText,
            finalized: this.finalizedText,
            combined: (this.finalizedText + " " + this.provisionalText).trim()
          });
        }
      };

      this.recognition.onerror = (event) => {
        console.warn("[AudioEngine] SpeechRecognition error:", event.error);
      };

      this.recognition.onend = () => {
        if (this.isRecording) {
          // Restart if still in recording state
          try { this.recognition.start(); } catch (e) {}
        }
      };
    } else {
      console.warn("[AudioEngine] Native SpeechRecognition API not supported. Falling back to typing / chunk mode.");
    }
  }

  async startMicrophone() {
    if (this.mediaStream) return true;

    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.audioContext = new AudioCtx();
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      this.analyser.smoothingTimeConstant = 0.8;

      this.sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream);
      this.sourceNode.connect(this.analyser);

      this.startVolumeMonitoring();
      return true;
    } catch (err) {
      console.error("[AudioEngine] Microphone permission denied or unavailable:", err);
      return false;
    }
  }

  stopMicrophone() {
    this.stopRecording();
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(t => t.stop());
      this.mediaStream = null;
    }
    if (this.audioContext && this.audioContext.state !== "closed") {
      this.audioContext.close();
      this.audioContext = null;
    }
  }

  startVolumeMonitoring() {
    if (!this.analyser) return;
    const dataArray = new Uint8Array(this.analyser.frequencyBinCount);

    const checkVolume = () => {
      if (!this.analyser) return;
      this.analyser.getByteFrequencyData(dataArray);

      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        sum += dataArray[i];
      }
      const avg = sum / dataArray.length;
      this.volume = Math.min(100, Math.round((avg / 128) * 100));

      if (this.onVolumeCallback) {
        this.onVolumeCallback(this.volume);
      }

      // Voice Activity threshold
      if (this.volume > 15 && this.isRecording) {
        this.handleUserVoiceActivity();
      }

      requestAnimationFrame(checkVolume);
    };
    checkVolume();
  }

  handleUserVoiceActivity() {
    if (!this.isSpeaking) {
      this.isSpeaking = true;
      if (this.onSpeechStartCallback) this.onSpeechStartCallback();
    }

    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
    }

    // Set timer for pause detection
    this.silenceTimer = setTimeout(() => {
      this.isSpeaking = false;
      if (this.onSpeechEndCallback) this.onSpeechEndCallback();
    }, this.silenceThresholdMs);
  }

  startRecording() {
    this.isRecording = true;
    this.provisionalText = "";
    this.finalizedText = "";

    if (this.recognition) {
      try {
        this.recognition.start();
      } catch (e) {
        // Already active
      }
    }
  }

  stopRecording() {
    this.isRecording = false;
    this.isSpeaking = false;
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }

    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (e) {}
    }

    const fullTranscript = (this.finalizedText + " " + this.provisionalText).trim();
    if (this.onFinalCallback && fullTranscript) {
      this.onFinalCallback(fullTranscript);
    }
    return fullTranscript;
  }

  drawWaveform(canvas) {
    if (!canvas || !this.analyser) return;
    const ctx = canvas.getContext("2d");
    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const render = () => {
      if (!this.analyser) return;
      this.analyser.getByteTimeDomainData(dataArray);

      ctx.fillStyle = "rgba(7, 9, 14, 0.3)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      ctx.lineWidth = 2;
      ctx.strokeStyle = this.isSpeaking ? "#38bdf8" : "#475569";
      ctx.beginPath();

      const sliceWidth = canvas.width / bufferLength;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = (v * canvas.height) / 2;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
        x += sliceWidth;
      }

      ctx.lineTo(canvas.width, canvas.height / 2);
      ctx.stroke();

      if (this.isRecording) {
        requestAnimationFrame(render);
      }
    };
    render();
  }
}

window.AudioEngine = AudioEngine;
