/**
 * Audio Engine for IMAIRA FairScore.
 * Handles microphone capture, Web Audio API AnalyserNode visualizer,
 * Voice Activity Detection (VAD), and resilient continuous streaming speech recognition (zero word limit).
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
    this.restartTimer = null;
    this.watchdogTimer = null;

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
      try {
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.maxAlternatives = 1;
        this.recognition.lang = "en-US";

        this.recognition.onstart = () => {
          console.log("[AudioEngine] Continuous SpeechRecognition stream active");
        };

        this.recognition.onresult = (event) => {
          let interim = "";
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            const piece = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              const clean = piece.trim();
              if (clean) {
                this.finalizedText += (this.finalizedText ? " " : "") + clean;
              }
            } else {
              interim += piece;
            }
          }
          this.provisionalText = interim;

          if (this.onInterimCallback) {
            this.onInterimCallback({
              provisional: this.provisionalText,
              finalized: this.finalizedText,
              combined: (this.finalizedText + " " + this.provisionalText).trim()
            });
          }
        };

        this.recognition.onerror = (event) => {
          const err = event.error;
          // 'no-speech' is a normal thinking pause; restart instantly without cutoff
          if (err === "no-speech" || err === "aborted") {
            if (this.isRecording) {
              this.scheduleRestart(80);
            }
            return;
          }
          if (err === "network") {
            if (this.isRecording) {
              this.scheduleRestart(400);
            }
            return;
          }
          console.warn("[AudioEngine] SpeechRecognition warning:", err);
        };

        this.recognition.onend = () => {
          // Commit any pending provisional text so words right before a pause are never dropped
          if (this.provisionalText && this.provisionalText.trim()) {
            this.finalizedText += (this.finalizedText ? " " : "") + this.provisionalText.trim();
            this.provisionalText = "";
            if (this.onInterimCallback) {
              this.onInterimCallback({
                provisional: "",
                finalized: this.finalizedText,
                combined: this.finalizedText
              });
            }
          }

          // Safe debounced restart for seamless, infinite continuous listening
          if (this.isRecording) {
            this.scheduleRestart(80);
          }
        };
      } catch (e) {
        console.error("[AudioEngine] Failed to initialize SpeechRecognition:", e);
      }
    } else {
      console.warn("[AudioEngine] Native SpeechRecognition API not supported. Falling back to typing / chunk mode.");
    }
  }

  scheduleRestart(delayMs = 80) {
    if (this.restartTimer) {
      clearTimeout(this.restartTimer);
    }
    this.restartTimer = setTimeout(() => {
      if (!this.isRecording || !this.recognition) return;
      try {
        this.recognition.start();
      } catch (err) {
        if (err.name === "InvalidStateError") {
          this.restartTimer = setTimeout(() => {
            if (this.isRecording && this.recognition) {
              try { this.recognition.start(); } catch (_) {
                this.rebuildRecognition();
              }
            }
          }, 200);
        } else {
          this.rebuildRecognition();
        }
      }
    }, delayMs);
  }

  rebuildRecognition() {
    if (this.recognition) {
      try {
        this.recognition.onresult = null;
        this.recognition.onerror = null;
        this.recognition.onend = null;
        this.recognition.abort();
      } catch (_) {}
    }
    this.initSpeechRecognition();
    if (this.isRecording && this.recognition) {
      setTimeout(() => {
        if (this.isRecording && this.recognition) {
          try { this.recognition.start(); } catch (_) {}
        }
      }, 150);
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

      requestAnimationFrame(checkVolume);
    };
    checkVolume();
  }

  startRecording() {
    this.isRecording = true;
    this.provisionalText = "";
    this.finalizedText = "";

    if (!this.recognition) {
      this.initSpeechRecognition();
    }

    if (this.recognition) {
      try {
        this.recognition.start();
      } catch (e) {
        if (e.name === "InvalidStateError") {
          this.scheduleRestart(100);
        }
      }
    }

    // Keep-alive watchdog timer
    if (this.watchdogTimer) clearInterval(this.watchdogTimer);
    this.watchdogTimer = setInterval(() => {
      if (this.isRecording && this.recognition) {
        try {
          this.recognition.start();
        } catch (_) {}
      }
    }, 3000);
  }

  stopRecording() {
    this.isRecording = false;
    this.isSpeaking = false;
    if (this.restartTimer) {
      clearTimeout(this.restartTimer);
      this.restartTimer = null;
    }
    if (this.watchdogTimer) {
      clearInterval(this.watchdogTimer);
      this.watchdogTimer = null;
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
      ctx.strokeStyle = this.isRecording ? "#38bdf8" : "#475569";
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
