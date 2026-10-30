export type InterviewStage =
  | 'GREETING'
  | 'INTRODUCTION'
  | 'TECHNICAL_QUESTION'
  | 'FOLLOW_UP'
  | 'CANDIDATE_QUESTIONS'
  | 'CONCLUDED';

export interface CandidateConfig {
  name: string;
  domain: string;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  numQuestions: number;
}

export interface Question {
  id: string;
  question: string;
  category: string;
  difficulty: string;
  key_concepts?: string[];
  reference_answer?: string;
  rubric_id?: string;
}

export interface UtteranceTurn {
  id: string;
  speaker: 'ai' | 'candidate';
  text: string;
  timestamp: number;
  stage?: InterviewStage;
  auditLog?: Array<{
    original_text: string;
    verified_text: string;
    reason: string;
  }>;
}

export interface InterviewSession {
  sessionId: string;
  candidateName: string;
  domain: string;
  difficulty: string;
  stage: InterviewStage;
  currentQuestion?: Question;
  questionIndex: number;
  totalQuestions: number;
  turns: UtteranceTurn[];
  isConcluded: boolean;
  startTime: number;
}
