import { Question, UtteranceTurn } from './interview';

export interface HealthResponse {
  status: string;
  timestamp: string;
  calibrators_loaded: boolean;
  glossary_terms_loaded: number;
  rubrics_loaded: number;
  port: number;
}

export interface StartInterviewRequest {
  candidate_name: string;
  domain: string;
  difficulty: string;
  num_questions: number;
}

export interface StartInterviewResponse {
  status: string;
  session_id: string;
  greeting: string;
  first_question: Question;
  domain: string;
  difficulty: string;
  total_questions: number;
}

export interface InterviewTurnRequest {
  session_id: string;
  candidate_utterance: string;
  word_timings?: Array<{
    word: string;
    start: number;
    end: number;
    conf: number;
  }>;
  audio_base64?: string;
}

export interface InterviewTurnResponse {
  status: string;
  session_id: string;
  stage: string;
  ai_response: string;
  is_concluded: boolean;
  current_question?: Question;
  current_question_detail?: any;
  verified_candidate_utterance: string;
  raw_utterance?: string;
  recovered_utterance?: string;
  corrections_applied?: number;
  slice_recovery_log?: any[];
  audit_log: Array<{
    original_text: string;
    verified_text: string;
    reason: string;
    status?: string;
    confidence?: number;
  }>;
  evaluation?: any;
}

export interface ConcludeInterviewRequest {
  session_id: string;
  final_scorecard?: any;
}

export interface ConcludeInterviewResponse {
  status: string;
  session_id: string;
  stage: string;
  turns_count: number;
  final_scorecard: any;
  cumulative_dual_diagnosis?: any;
}

export interface ScoreRequest {
  session_id: string;
  question_id?: string;
  question_text?: string;
  transcript: Array<{
    start: number;
    end: number;
    speaker: string;
    text: string;
  }>;
}

export interface ScoreResponse {
  session_id: string;
  overall_score: number;
  scores: {
    content: number;
    structure: number;
    communication: number;
  };
  calibrated_scores: {
    content: number;
    structure: number;
    communication: number;
  };
  feedback: Array<{
    dimension: string;
    marks_lost: number;
    quote: string;
    fix_sentence: string;
  }>;
  flags: Record<string, 'covered' | 'partial' | 'missing'>;
  structure_diagnostics?: any;
  communication_diagnostics?: any;
}
