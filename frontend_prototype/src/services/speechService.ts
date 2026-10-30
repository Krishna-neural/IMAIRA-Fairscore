import { phoneticRecovery, RecoveryAuditItem } from './phoneticRecovery';

export interface SpeechRecognitionResult {
  provisional: string;
  finalized: string;
  recoveredTerms?: RecoveryAuditItem[];
}

export class SpeechService {
  private recognition: any = null;
  private isListening: boolean = false;
  private restartTimeout: any = null;
  private watchdogInterval: any = null;
  private interimCallback: ((res: SpeechRecognitionResult) => void) | null = null;
  private speechEndCallback: (() => void) | null = null;
  private finalizedBuffer: string = '';
  private currentProvisional: string = '';
  private isMuted: boolean = false;
  private currentUtterance: SpeechSynthesisUtterance | null = null;
  private mouthMovementCallback: ((isOpen: boolean, viseme: number) => void) | null = null;
  private mouthAnimInterval: any = null;
  private currentLang: string =
    typeof navigator !== 'undefined' &&
    (navigator.language === 'en-IN' || (navigator as any).languages?.includes('en-IN'))
      ? 'en-IN'
      : 'en-US';

  constructor() {
    this.initRecognition();
  }

  private initRecognition() {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      console.warn('[SpeechService] Web Speech API not supported in this browser.');
      return;
    }

    try {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.maxAlternatives = 1;
      this.recognition.lang = this.currentLang;

      this.recognition.onstart = () => {
        // Recognition stream active
      };

      this.recognition.onresult = (event: any) => {
        let interim = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const piece = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            const clean = piece.trim();
            if (clean) {
              this.finalizedBuffer += (this.finalizedBuffer ? ' ' : '') + clean;
            }
          } else {
            interim += piece;
          }
        }
        this.currentProvisional = interim;

        // Stage 1 Real-time Acoustic & Phonetic Technical Recovery
        const recoveredFinal = phoneticRecovery.recoverText(this.finalizedBuffer);
        const recoveredInterim = phoneticRecovery.recoverText(this.currentProvisional);
        const allRecoveries = [...recoveredFinal.auditItems, ...recoveredInterim.auditItems];

        if (this.interimCallback) {
          this.interimCallback({
            provisional: recoveredInterim.text,
            finalized: recoveredFinal.text,
            recoveredTerms: allRecoveries,
          });
        }
      };

      this.recognition.onerror = (err: any) => {
        const errType = err?.error;
        // 'no-speech' is a normal pause between sentences or thinking pauses.
        // Chrome drops the connection on pause; we schedule an instant seamless restart.
        if (errType === 'no-speech' || errType === 'aborted') {
          if (this.isListening) {
            this.scheduleSafeRestart(80);
          }
          return;
        }
        if (errType === 'network') {
          console.warn('[SpeechService] Transient network glitch, re-arming...');
          if (this.isListening) {
            this.scheduleSafeRestart(400);
          }
          return;
        }
        console.warn('[SpeechService] SpeechRecognition event:', errType);
      };

      this.recognition.onend = () => {
        // Commit any uncommitted provisional text so words right before a pause are never lost
        if (this.currentProvisional && this.currentProvisional.trim()) {
          this.finalizedBuffer += (this.finalizedBuffer ? ' ' : '') + this.currentProvisional.trim();
          this.currentProvisional = '';
          if (this.interimCallback) {
            this.interimCallback({
              provisional: '',
              finalized: this.finalizedBuffer,
            });
          }
        }

        // Seamless auto-restart: Web Speech API continuously listens with zero word limit
        if (this.isListening) {
          this.scheduleSafeRestart(80);
        }
      };
    } catch (e) {
      console.error('[SpeechService] Error initializing recognition:', e);
    }
  }

  private scheduleSafeRestart(delayMs = 80) {
    if (this.restartTimeout) {
      clearTimeout(this.restartTimeout);
    }
    this.restartTimeout = setTimeout(() => {
      if (!this.isListening || !this.recognition) return;
      try {
        this.recognition.start();
      } catch (err: any) {
        if (err?.name === 'InvalidStateError') {
          // Browser is still shutting down previous session; retry with slight backoff
          this.restartTimeout = setTimeout(() => {
            if (this.isListening && this.recognition) {
              try {
                this.recognition.start();
              } catch (_) {
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

  private rebuildRecognition() {
    if (this.recognition) {
      try {
        this.recognition.onresult = null;
        this.recognition.onerror = null;
        this.recognition.onend = null;
        this.recognition.abort();
      } catch (_) {}
    }
    this.initRecognition();
    if (this.isListening && this.recognition) {
      setTimeout(() => {
        if (this.isListening && this.recognition) {
          try {
            this.recognition.start();
          } catch (_) {}
        }
      }, 150);
    }
  }

  startListening(
    onInterim: (res: SpeechRecognitionResult) => void,
    onSpeechEnd?: () => void
  ) {
    this.interimCallback = onInterim;
    this.speechEndCallback = onSpeechEnd || null;
    this.finalizedBuffer = '';
    this.currentProvisional = '';
    this.isListening = true;

    if (!this.recognition) {
      this.initRecognition();
    }

    if (this.recognition) {
      try {
        this.recognition.start();
      } catch (e: any) {
        if (e?.name === 'InvalidStateError') {
          this.scheduleSafeRestart(100);
        }
      }
    }

    // Keep-alive watchdog: periodically verifies recognition is alive while listening
    if (this.watchdogInterval) clearInterval(this.watchdogInterval);
    this.watchdogInterval = setInterval(() => {
      if (this.isListening && this.recognition) {
        try {
          this.recognition.start();
        } catch (_) {
          // If already running, InvalidStateError is normal and expected
        }
      }
    }, 3000);
  }

  resetBuffer() {
    this.finalizedBuffer = '';
    this.currentProvisional = '';
    if (this.interimCallback) {
      this.interimCallback({
        provisional: '',
        finalized: '',
      });
    }
  }

  setLanguage(lang: string) {
    this.currentLang = lang;
    if (this.recognition) {
      try {
        this.recognition.lang = lang;
      } catch (_) {}
    }
  }

  getLanguage(): string {
    return this.currentLang;
  }

  setFinalizedBuffer(text: string) {
    this.finalizedBuffer = text;
    this.currentProvisional = '';
    const rec = phoneticRecovery.recoverText(text);
    if (this.interimCallback) {
      this.interimCallback({
        provisional: '',
        finalized: rec.text,
        recoveredTerms: rec.auditItems,
      });
    }
  }

  stopListening(): string {
    this.isListening = false;
    if (this.restartTimeout) {
      clearTimeout(this.restartTimeout);
      this.restartTimeout = null;
    }
    if (this.watchdogInterval) {
      clearInterval(this.watchdogInterval);
      this.watchdogInterval = null;
    }

    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (_) {}
    }

    const rawUtterance = (this.finalizedBuffer + ' ' + this.currentProvisional).trim();
    const recovered = phoneticRecovery.recoverText(rawUtterance);
    this.finalizedBuffer = '';
    this.currentProvisional = '';
    return recovered.text;
  }

  setMuted(muted: boolean) {
    this.isMuted = muted;
    if (muted && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      this.stopMouthAnimation();
    }
  }

  onMouthMovement(callback: (isOpen: boolean, viseme: number) => void) {
    this.mouthMovementCallback = callback;
  }

  speak(text: string, onDone?: () => void) {
    if (this.isMuted || !('speechSynthesis' in window)) {
      if (onDone) onDone();
      return;
    }

    window.speechSynthesis.cancel();
    this.stopMouthAnimation();

    const utterance = new SpeechSynthesisUtterance(text);
    this.currentUtterance = utterance;
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    // Pick a natural English voice if available
    const voices = window.speechSynthesis.getVoices();
    const naturalVoice = voices.find(
      (v) =>
        v.lang.startsWith('en') &&
        (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Samantha') || v.name.includes('Daniel'))
    );
    if (naturalVoice) utterance.voice = naturalVoice;

    // Synchronize mouth animation
    utterance.onstart = () => {
      this.startMouthAnimation();
    };

    utterance.onboundary = (event) => {
      if (event.name === 'word' && this.mouthMovementCallback) {
        const viseme = Math.floor(Math.random() * 4) + 1; // 1 to 4 mouth shapes
        this.mouthMovementCallback(true, viseme);
      }
    };

    utterance.onend = () => {
      this.stopMouthAnimation();
      if (onDone) onDone();
    };

    utterance.onerror = () => {
      this.stopMouthAnimation();
      if (onDone) onDone();
    };

    window.speechSynthesis.speak(utterance);
  }

  private startMouthAnimation() {
    this.stopMouthAnimation();
    let toggle = false;
    this.mouthAnimInterval = setInterval(() => {
      toggle = !toggle;
      if (this.mouthMovementCallback) {
        const viseme = toggle ? Math.floor(Math.random() * 3) + 1 : 0;
        this.mouthMovementCallback(toggle, viseme);
      }
    }, 140);
  }

  private stopMouthAnimation() {
    if (this.mouthAnimInterval) {
      clearInterval(this.mouthAnimInterval);
      this.mouthAnimInterval = null;
    }
    if (this.mouthMovementCallback) {
      this.mouthMovementCallback(false, 0);
    }
  }

  stopSpeaking() {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    this.stopMouthAnimation();
  }
}

export const speechService = new SpeechService();
