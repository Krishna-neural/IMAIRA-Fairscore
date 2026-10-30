import React from 'react';
import { ScoreCard } from '../components/evaluation/ScoreCard';
import { RubricCoverage } from '../components/evaluation/RubricCoverage';
import { CoachingFeedback } from '../components/evaluation/CoachingFeedback';
import { AuditLogTable } from '../components/evaluation/AuditLogTable';
import { EvaluationResult } from '../types/evaluation';

interface EvaluationPageProps {
  result: EvaluationResult | null;
  candidateName: string;
  domain: string;
  onStartNew: () => void;
  onExploreJudge: () => void;
}

export const EvaluationPage: React.FC<EvaluationPageProps> = ({
  result,
  candidateName,
  domain,
  onStartNew,
  onExploreJudge,
}) => {
  if (!result) {
    return (
      <div className="max-w-xl mx-auto py-16 text-center space-y-4">
        <h2 className="text-xl font-bold text-[#101C35]">No Evaluation Completed Yet</h2>
        <p className="text-xs text-slate-500">
          Please complete a mock technical interview session to generate your multi-dimensional performance evaluation scorecard.
        </p>
        <button
          onClick={onStartNew}
          className="px-5 py-2.5 bg-[#2457A6] hover:bg-[#1A4482] text-white text-xs font-bold rounded shadow-xs transition-colors"
        >
          Start an Interview
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 space-y-6">
      <ScoreCard
        overallScore={result.overallScore}
        scores={result.scores}
        calibratedScores={result.calibratedScores}
        candidateName={candidateName}
        domain={domain}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <RubricCoverage flags={result.flags} />
        <CoachingFeedback feedback={result.feedback} />
      </div>

      <AuditLogTable auditLog={result.auditLog} />

      <div className="flex justify-center gap-3 pt-4">
        <button
          onClick={onStartNew}
          className="px-5 py-2.5 bg-[#2457A6] hover:bg-[#1A4482] text-white text-xs font-bold rounded shadow-xs transition-colors"
        >
          Start Another Interview
        </button>
        <button
          onClick={onExploreJudge}
          className="px-5 py-2.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 text-xs font-semibold rounded shadow-xs transition-colors"
        >
          Inspect Judge Technical Console
        </button>
      </div>
    </div>
  );
};
