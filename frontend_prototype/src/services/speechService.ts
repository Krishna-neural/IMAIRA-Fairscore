export interface SpeechRecognitionResult {
  provisional: string;
  finalized: string;
}

export class SpeechService {
  private recognition: any = null;
  private isListening: boolean = false;
  private interimCallback: ((res: SpeechRecognitionResult) => void) | null = null;
  private speechEndCallback: (() => void) | null = null;
  private finalizedBuffer: string = '';
  private currentProvisional: string = '';
  private isMuted: boolean = false;
  private currentUtterance: SpeechSynthesisUtterance | null = null;
  private mouthMovementCallback: ((isOpen: boolean, viseme: number) => void) | null = null;
  private mouthAnimInterval: any = null;

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

    this.recognition = new SpeechRecognition();
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.lang = 'en-US';

    this.recognition.onresult = (event: any) => {
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          this.finalizedBuffer += (this.finalizedBuffer ? ' ' : '') + transcript.trim();
        } else {
          interim += transcript;
        }
      }
      this.currentProvisional = interim;

      if (this.interimCallback) {
        this.interimCallback({
          provisional: this.currentProvisional,
          finalized: this.finalizedBuffer,
        });
      }
    };

    this.recognition.onerror = (err: any) => {
      if (err.error !== 'no-speech') {
        console.warn('[SpeechService] Recognition error:', err.error);
      }
    };

    this.recognition.onend = () => {
      if (this.isListening) {
        try {
          this.recognition.start();
        } catch (_) {}
      }
    };
  }

  startListening(
    onInterim: (res: SpeechRecognitionResult) => void,
    onSpeechEnd?: () => void
  ) {
    if (!this.recognition) return;
    this.interimCallback = onInterim;
    this.speechEndCallback = onSpeechEnd || null;
    this.finalizedBuffer = '';
    this.currentProvisional = '';
    this.isListening = true;

    try {
      this.recognition.start();
    } catch (_) {}
  }

  stopListening(): string {
    this.isListening = false;
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (_) {}
    }
    const fullUtterance = (this.finalizedBuffer + ' ' + this.currentProvisional).trim();
    this.finalizedBuffer = '';
    this.currentProvisional = '';
    return fullUtterance;
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
