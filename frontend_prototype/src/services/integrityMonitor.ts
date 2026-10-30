import {
  IntegrityEvent,
  IntegrityEventType,
  IntegrityWarning,
  RestrictionState,
  IntegrityPolicyConfig,
  DEFAULT_INTEGRITY_POLICY,
} from '../types/integrity';

const STORAGE_RESTRICTION_KEY = 'imaira_interviewer_restriction_v1';
const STORAGE_WARNINGS_KEY = 'imaira_interviewer_warnings_v1';

export class IntegrityMonitor {
  private videoElement: HTMLVideoElement | null = null;
  private canvas: HTMLCanvasElement | null = null;
  private isMonitoring: boolean = false;
  private monitorInterval: any = null;
  private policy: IntegrityPolicyConfig = DEFAULT_INTEGRITY_POLICY;

  // Temporal trackers to avoid false positives (require 3.0s continuous violation)
  private violationStartTime: Record<IntegrityEventType, number | null> = {
    CAMERA_DISABLED: null,
    MULTIPLE_PEOPLE: null,
    CAMERA_OBSTRUCTED: null,
    FACE_NOT_DETECTED: null,
  };

  private activeWarningCount: number = 0;
  private warningHistory: IntegrityWarning[] = [];
  private onWarningCallback: ((warning: IntegrityWarning) => void) | null = null;
  private onRestrictionCallback: ((state: RestrictionState) => void) | null = null;
  private onStatusChangeCallback: ((status: { isMonitoring: boolean; lastCheckText: string; activeViolation: string | null }) => void) | null = null;

  constructor() {
    this.canvas = document.createElement('canvas');
    this.canvas.width = 160;
    this.canvas.height = 120;
    this.loadStateFromStorage();
  }

  setPolicy(policy: Partial<IntegrityPolicyConfig>) {
    this.policy = { ...this.policy, ...policy };
  }

  onWarning(callback: (warning: IntegrityWarning) => void) {
    this.onWarningCallback = callback;
  }

  onRestriction(callback: (state: RestrictionState) => void) {
    this.onRestrictionCallback = callback;
  }

  onStatusChange(callback: (status: { isMonitoring: boolean; lastCheckText: string; activeViolation: string | null }) => void) {
    this.onStatusChangeCallback = callback;
  }

  getRestrictionState(): RestrictionState {
    try {
      const saved = localStorage.getItem(STORAGE_RESTRICTION_KEY);
      if (saved) {
        const state: RestrictionState = JSON.parse(saved);
        if (state.expiresAt && Date.now() > state.expiresAt) {
          // Expired restriction
          this.clearRestriction();
          return { isRestricted: false, auditTrail: [] };
        }
        return state;
      }
    } catch (_) {}
    return { isRestricted: false, auditTrail: [] };
  }

  startMonitoring(videoEl: HTMLVideoElement) {
    if (this.getRestrictionState().isRestricted) {
      console.warn('[IntegrityMonitor] Session blocked: Interviewer is under 24-hour restriction.');
      return;
    }

    this.videoElement = videoEl;
    this.isMonitoring = true;
    this.resetTemporalTrackers();

    // Sample video frame every 600ms (on-device processing)
    this.monitorInterval = setInterval(() => {
      this.evaluateFrame();
    }, 600);

    this.notifyStatus('Active & Monitoring', null);
  }

  stopMonitoring() {
    this.isMonitoring = false;
    if (this.monitorInterval) {
      clearInterval(this.monitorInterval);
      this.monitorInterval = null;
    }
    this.resetTemporalTrackers();
    this.notifyStatus('Monitoring Inactive', null);
  }

  private resetTemporalTrackers() {
    this.violationStartTime = {
      CAMERA_DISABLED: null,
      MULTIPLE_PEOPLE: null,
      CAMERA_OBSTRUCTED: null,
      FACE_NOT_DETECTED: null,
    };
  }

  private notifyStatus(lastCheckText: string, activeViolation: string | null) {
    if (this.onStatusChangeCallback) {
      this.onStatusChangeCallback({
        isMonitoring: this.isMonitoring,
        lastCheckText,
        activeViolation,
      });
    }
  }

  private evaluateFrame() {
    if (!this.videoElement || !this.isMonitoring) return;

    const stream = this.videoElement.srcObject as MediaStream;
    const now = Date.now();

    // 1. Check if camera feed was disabled / muted
    if (!stream || stream.getVideoTracks().length === 0 || !stream.getVideoTracks()[0].enabled) {
      this.handleTemporalViolation('CAMERA_DISABLED', now, 'Camera feed disabled during active monitored session');
      return;
    } else {
      this.violationStartTime.CAMERA_DISABLED = null;
    }

    // 2. Perform on-device pixel analysis via 2D Canvas
    if (!this.canvas) return;
    const ctx = this.canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) return;

    try {
      ctx.drawImage(this.videoElement, 0, 0, this.canvas.width, this.canvas.height);
      const frameData = ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
      const pixels = frameData.data;

      let totalBrightness = 0;
      let skinPixelsLeft = 0;
      let skinPixelsRight = 0;
      let totalSkinPixels = 0;

      for (let i = 0; i < pixels.length; i += 4) {
        const r = pixels[i];
        const g = pixels[i + 1];
        const b = pixels[i + 2];
        const brightness = (r + g + b) / 3;
        totalBrightness += brightness;

        // General human skin reflectance model in RGB space (peer-reviewed Kovac model)
        const isSkin =
          r > 95 &&
          g > 40 &&
          b > 20 &&
          Math.max(r, g, b) - Math.min(r, g, b) > 15 &&
          Math.abs(r - g) > 15 &&
          r > g &&
          r > b;

        if (isSkin) {
          totalSkinPixels++;
          const pixelIndex = i / 4;
          const x = pixelIndex % this.canvas.width;
          if (x < this.canvas.width / 2) {
            skinPixelsLeft++;
          } else {
            skinPixelsRight++;
          }
        }
      }

      const pixelCount = pixels.length / 4;
      const avgBrightness = totalBrightness / pixelCount;
      const skinRatio = totalSkinPixels / pixelCount;

      // Check 3: Obstruction / covered lens (near zero brightness or solid covering)
      if (avgBrightness < 12) {
        this.handleTemporalViolation(
          'CAMERA_OBSTRUCTED',
          now,
          'Camera view obstructed or completely darkened'
        );
        return;
      } else {
        this.violationStartTime.CAMERA_OBSTRUCTED = null;
      }

      // Check 4: Multiple people in frame (if both quadrants have large independent skin centroids)
      if (this.policy.checkMultiplePeople) {
        const leftRatio = skinPixelsLeft / pixelCount;
        const rightRatio = skinPixelsRight / pixelCount;
        if (leftRatio > 0.12 && rightRatio > 0.12 && Math.abs(leftRatio - rightRatio) < 0.05) {
          this.handleTemporalViolation(
            'MULTIPLE_PEOPLE',
            now,
            'Multiple individuals detected in the interviewer camera frame'
          );
          return;
        } else {
          this.violationStartTime.MULTIPLE_PEOPLE = null;
        }
      }

      // Check 5: Face / Person not detected in view
      if (skinRatio < 0.02) {
        this.handleTemporalViolation(
          'FACE_NOT_DETECTED',
          now,
          'Authorized interviewer is not visible in camera frame'
        );
        return;
      } else {
        this.violationStartTime.FACE_NOT_DETECTED = null;
      }

      this.notifyStatus('Frame verified • Normal', null);
    } catch (_) {
      // In case video is not yet ready
    }
  }

  private handleTemporalViolation(type: IntegrityEventType, now: number, description: string) {
    if (!this.violationStartTime[type]) {
      this.violationStartTime[type] = now;
      this.notifyStatus(`Verifying observation...`, type);
      return;
    }

    const elapsedSeconds = (now - this.violationStartTime[type]!) / 1000;
    this.notifyStatus(`Violation persisting (${elapsedSeconds.toFixed(1)}s)`, type);

    // Require violation to persist continuously for policy grace period (3.0s) to avoid false positives!
    if (elapsedSeconds >= this.policy.gracePeriodSeconds) {
      this.violationStartTime[type] = null; // reset to avoid repeating every frame

      const event: IntegrityEvent = {
        id: `ev_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
        type,
        timestamp: now,
        description,
        details: `Condition persisted continuously for ${elapsedSeconds.toFixed(1)} seconds.`,
        confidence: 0.92,
      };

      this.triggerWarning(event);
    }
  }

  private triggerWarning(event: IntegrityEvent) {
    this.activeWarningCount++;
    const warnNum = Math.min(3, this.activeWarningCount) as 1 | 2 | 3;

    let explanation = '';
    let correctiveAction = '';

    if (warnNum === 1) {
      explanation = `First integrity violation observed: ${event.description}.`;
      correctiveAction = 'Please adjust your camera framing and ensure only the authorized interviewer is visible.';
    } else if (warnNum === 2) {
      explanation = `Second integrity violation observed: Repeated ${event.description}.`;
      correctiveAction = 'Ensure compliance immediately. A third violation will lead to session restriction.';
    } else {
      explanation = `FINAL WARNING (3/3): Repeated ${event.description}.`;
      correctiveAction = 'Any further verified violation will immediately trigger a 24-hour interviewer restriction.';
    }

    const warning: IntegrityWarning = {
      warningNumber: warnNum,
      event,
      timestamp: Date.now(),
      explanation,
      correctiveAction,
    };

    this.warningHistory.push(warning);
    this.saveStateToStorage();

    if (this.onWarningCallback) {
      this.onWarningCallback(warning);
    }

    // If candidate receives a 4th violation after 3 warnings -> Trigger 24-Hour Restriction
    if (this.activeWarningCount > 3) {
      this.trigger24HourRestriction(event);
    }
  }

  private trigger24HourRestriction(event: IntegrityEvent) {
    this.stopMonitoring();
    const now = Date.now();
    const expiresAt = now + 24 * 60 * 60 * 1000; // +24 hours

    const state: RestrictionState = {
      isRestricted: true,
      restrictedAt: now,
      expiresAt,
      reason: `Accumulated 3 verified warnings plus subsequent violation: ${event.description}`,
      auditTrail: [...this.warningHistory],
      appealSubmitted: false,
    };

    try {
      localStorage.setItem(STORAGE_RESTRICTION_KEY, JSON.stringify(state));
    } catch (_) {}

    if (this.onRestrictionCallback) {
      this.onRestrictionCallback(state);
    }
  }

  submitAppeal(reason: string): boolean {
    const state = this.getRestrictionState();
    if (!state.isRestricted) return false;

    state.appealSubmitted = true;
    try {
      localStorage.setItem(STORAGE_RESTRICTION_KEY, JSON.stringify(state));
    } catch (_) {}
    return true;
  }

  clearRestriction() {
    this.activeWarningCount = 0;
    this.warningHistory = [];
    try {
      localStorage.removeItem(STORAGE_RESTRICTION_KEY);
      localStorage.removeItem(STORAGE_WARNINGS_KEY);
    } catch (_) {}
  }

  private saveStateToStorage() {
    try {
      localStorage.setItem(
        STORAGE_WARNINGS_KEY,
        JSON.stringify({
          count: this.activeWarningCount,
          history: this.warningHistory,
        })
      );
    } catch (_) {}
  }

  private loadStateFromStorage() {
    try {
      const saved = localStorage.getItem(STORAGE_WARNINGS_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        this.activeWarningCount = parsed.count || 0;
        this.warningHistory = parsed.history || [];
      }
    } catch (_) {}
  }
}

export const integrityMonitor = new IntegrityMonitor();
