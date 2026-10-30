export interface DimensionScores {
  content: number;
  structure: number;
  communication: number;
}

export interface CalibratedScores {
  content: number;
  structure: number;
  communication: number;
}

export interface FeedbackItem {
  dimension: string;
  marks_lost: number;
  quote: string;
  fix_sentence: string;
}

export interface TerminologyAuditItem {
  timestamp_range: string;
  raw_token: string;
  verified_token: string;
  status: 'CORRECTED' | 'ABSTAINED';
  reason: string;
}

export interface EvaluationResult {
  sessionId: string;
  overallScore: number;
  scores: DimensionScores;
  calibratedScores: CalibratedScores;
  feedback: FeedbackItem[];
  flags: Record<string, 'covered' | 'partial' | 'missing'>;
  auditLog: TerminologyAuditItem[];
  structureDiagnostics?: {
    framing_score?: number;
    coherence_score?: number;
    closure_score?: number;
  };
  communicationDiagnostics?: {
    wpm?: number;
    filler_count?: number;
    pause_count?: number;
  };
}
