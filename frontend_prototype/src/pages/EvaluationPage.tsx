import React, { useState } from 'react';
import { ScoreCard } from '../components/evaluation/ScoreCard';
import { DualDiagnosisPanel } from '../components/evaluation/DualDiagnosisPanel';
import { RubricCoverage } from '../components/evaluation/RubricCoverage';
import { CoachingFeedback } from '../components/evaluation/CoachingFeedback';
import { AuditLogTable } from '../components/evaluation/AuditLogTable';
import { EvaluationResult } from '../types/evaluation';
import { ChevronDown, ChevronUp, MessageSquare, CheckCircle, Volume2 } from 'lucide-react';

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
  const [showTurnHistory, setShowTurnHistory] = useState(false);

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

  const candidateTurns = (result.turns || []).filter(
    (t: any) => t.speaker === 'candidate' || t.speaker === 'Candidate'
  );

  return (
    <div className="max-w-5xl mx-auto py-8 space-y-6">
      {/* 1. Main ScoreCard (60% Content + 40% Structure) */}
      <ScoreCard
        overallScore={result.overallScore}
        scores={result.scores}
        calibratedScores={result.calibratedScores}
        candidateName={candidateName}
        domain={domain}
        summaryVerdict={result.summaryVerdict}
      />

      {/* 2. Core Feature: Dual Diagnosis Panel (Technical Knowledge Gaps vs Accent/Pronunciation Coaching) */}
      <DualDiagnosisPanel
        dualDiagnosis={result.dualDiagnosis}
        feedback={result.feedback}
      />

      {/* 3. Semantic Rubric Coverage & Targeted Coaching Recommendations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <RubricCoverage flags={result.flags} />
        <CoachingFeedback feedback={result.feedback} />
      </div>

      {/* 4. Acoustic Verification & Terminology Audit Trail */}
      <AuditLogTable auditLog={result.auditLog} />

      {/* 5. Interactive Turn-by-Turn Inspection (Optional Expansion) */}
      {candidateTurns.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
          <button
            onClick={() => setShowTurnHistory(!showTurnHistory)}
            className="w-full flex items-center justify-between text-left"
          >
            <div className="flex items-center gap-2">
              <MessageSquare size={16} className="text-[#2457A6]" />
              <h4 className="text-sm font-bold text-[#101C35]">
                Turn-by-Turn Transcript & Recovery Deep-Dive ({candidateTurns.length} Responses)
              </h4>
            </div>
            {showTurnHistory ? (
              <ChevronUp size={16} className="text-slate-500" />
            ) : (
              <ChevronDown size={16} className="text-slate-500" />
            )}
          </button>

          {showTurnHistory && (
            <div className="mt-4 space-y-3 pt-3 border-t border-slate-100">
              {candidateTurns.map((turn: any, idx: number) => {
                const evalObj = turn.evaluation;
                const sliceLogs = turn.slice_recovery_log || [];

                return (
                  <div
                    key={idx}
                    className="p-3 bg-slate-50 border border-slate-200 rounded-md text-xs space-y-2"
                  >
                    <div className="flex items-center justify-between text-[11px] font-bold text-slate-700">
                      <span>Turn #{idx + 1} {turn.question_id ? `• ${turn.question_id}` : ''}</span>
                      {evalObj?.scores && (
                        <span className="text-[#2457A6]">
                          Score: {evalObj.scores.content_pct}% Content • {evalObj.scores.structure_pct}% Structure
                        </span>
                      )}
                    </div>

                    {turn.question_text && (
                      <div className="text-slate-800 font-semibold text-[11px]">
                        Q: {turn.question_text}
                      </div>
                    )}

                    <div className="space-y-1">
                      <div className="text-slate-500 text-[10px] uppercase font-bold">
                        Candidate Answer (Recovered):
                      </div>
                      <p className="text-slate-900 bg-white p-2 rounded border border-slate-200 font-medium">
                        "{turn.recovered_utterance || turn.text}"
                      </p>
                    </div>

                    {turn.raw_utterance && turn.raw_utterance !== turn.recovered_utterance && (
                      <div className="space-y-0.5">
                        <div className="text-slate-400 text-[10px] uppercase font-bold">
                          Raw Speech Input:
                        </div>
                        <p className="text-slate-500 italic bg-white p-1.5 rounded border border-slate-200 text-[11px]">
                          "{turn.raw_utterance}"
                        </p>
                      </div>
                    )}

                    {sliceLogs.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5 pt-1">
                        <span className="text-[10px] text-emerald-800 font-bold flex items-center gap-1">
                          <CheckCircle size={11} />
                          Recovered Spans:
                        </span>
                        {sliceLogs.map((log: any, lIdx: number) => (
                          <span
                            key={lIdx}
                            className="px-1.5 py-0.5 bg-emerald-50 text-emerald-900 border border-emerald-200 rounded text-[10px] font-mono"
                          >
                            "{log.raw_span || log.raw_token}" → {log.replacement || log.verified_token}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* 6. Navigation Actions */}
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
