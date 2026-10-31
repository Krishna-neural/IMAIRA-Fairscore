export type IntegrityEventType =
  | 'CAMERA_DISABLED'
  | 'MULTIPLE_PEOPLE'
  | 'CAMERA_OBSTRUCTED'
  | 'FACE_NOT_DETECTED';

export interface IntegrityEvent {
  id: string;
  type: IntegrityEventType;
  timestamp: number;
  description: string;
  details: string;
  confidence: number;
}

export interface IntegrityWarning {
  warningNumber: 1 | 2 | 3;
  event: IntegrityEvent;
  timestamp: number;
  explanation: string;
  correctiveAction: string;
}

export interface RestrictionState {
  isRestricted: boolean;
  restrictedAt?: number;
  expiresAt?: number;
  reason?: string;
  auditTrail: IntegrityWarning[];
  appealSubmitted?: boolean;
}

export interface IntegrityPolicyConfig {
  requireCamera: boolean;
  checkMultiplePeople: boolean;
  checkObstruction: boolean;
  gracePeriodSeconds: number; // minimum duration of violation before warning
  confidenceThreshold: number; // minimum detection confidence
}

export const DEFAULT_INTEGRITY_POLICY: IntegrityPolicyConfig = {
  requireCamera: true,
  checkMultiplePeople: true,
  checkObstruction: true,
  gracePeriodSeconds: 3.0,
  confidenceThreshold: 0.75,
};
