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

export interface TechnicalKnowledgeGap {
  question_id?: string;
  dimension?: string;
  missing_concepts?: string[];
  marks_lost: number;
  quote?: string;
  fix_sentence: string;
}

export interface PronunciationImprovement {
  question_id?: string;
  raw_token: string;
  recovered_token: string;
  coaching: string;
  marks_deducted: number;
}

export interface DualDiagnosis {
  technical_knowledge_gaps: TechnicalKnowledgeGap[];
  pronunciation_improvements: PronunciationImprovement[];
  accent_penalty_applied: boolean;
  acoustic_protection_active: boolean;
}

export interface EvaluationResult {
  sessionId: string;
  overallScore: number;
  scores: DimensionScores;
  calibratedScores: CalibratedScores;
  feedback: FeedbackItem[];
  flags: Record<string, 'covered' | 'partial' | 'missing'>;
  auditLog: TerminologyAuditItem[];
  dualDiagnosis?: DualDiagnosis;
  summaryVerdict?: string;
  questionsEvaluated?: number;
  turns?: any[];
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
