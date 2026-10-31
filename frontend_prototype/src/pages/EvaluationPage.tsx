import React, { useState } from 'react';
import { ScoreCard } from '../components/evaluation/ScoreCard';
import { DualDiagnosisPanel } from '../components/evaluation/DualDiagnosisPanel';
import { RubricCoverage } from '../components/evaluation/RubricCoverage';
import { CoachingFeedback } from '../components/evaluation/CoachingFeedback';
import { AuditLogTable } from '../components/evaluation/AuditLogTable';
import { HumanAvatar } from '../components/avatar/HumanAvatar';
import { speechService } from '../services/speechService';
import { EvaluationResult } from '../types/evaluation';
import { ChevronDown, ChevronUp, MessageSquare, CheckCircle, Volume2, Download, Terminal, Shield } from 'lucide-react';

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
  const [isSpeakingDebrief, setIsSpeakingDebrief] = useState(false);
  const [activeTab, setActiveTab] = useState<'coaching' | 'audit'>('coaching');

  if (!result) {
    return (
      <div className="max-w-xl mx-auto py-16 text-center space-y-4">
        <div className="w-12 h-12 rounded-xl bg-surface-container-high border border-outline-variant/40 flex items-center justify-center text-primary mx-auto">
          <Terminal size={24} />
        </div>
        <h2 className="text-xl font-bold text-on-surface">No Evaluation Dossier Found</h2>
        <p className="text-xs text-outline font-mono">
          Please complete a mock technical interview session to generate your multi-dimensional performance evaluation scorecard.
        </p>
        <button
          onClick={onStartNew}
          className="px-5 py-2.5 bg-primary-container hover:bg-primary-fixed-dim text-on-primary-container text-xs font-mono font-bold rounded-lg shadow-sm transition-all"
        >
          Start an Interview
        </button>
      </div>
    );
  }

  const debriefSpeechText = `Hello ${candidateName || 'Candidate'}. That concludes your technical interview in ${domain}. You achieved an overall FairScore of ${result.overallScore} percent. Your Content Mastery was evaluated at ${result.scores.content} percent, with Structure and Flow at ${result.scores.structure} percent. Under our acoustic slice recovery, any pronunciation shifts or regional accent variations were protected with zero mark deductions. Please review your detailed technical knowledge gaps and coaching scope below.`;

  const handleToggleDebriefAudio = () => {
    if (isSpeakingDebrief) {
      speechService.setMuted(true);
      setIsSpeakingDebrief(false);
      setTimeout(() => speechService.setMuted(false), 200);
    } else {
      setIsSpeakingDebrief(true);
      speechService.speak(debriefSpeechText, () => {
        setIsSpeakingDebrief(false);
      });
    }
  };

  const handleExportJSON = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(result, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `imaira_fairscore_${result.sessionId || 'dossier'}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const candidateTurns = (result.turns || []).filter(
    (t: any) => t.speaker === 'candidate' || t.speaker === 'Candidate'
  );

  return (
    <div className="max-w-[1440px] mx-auto py-6 px-4 sm:px-6 space-y-6">
      {/* 0. Executive Verdict with Virtual Human Interviewer Debrief */}
      <div className="bg-surface-container-low border border-outline-variant/30 rounded-xl p-6 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)] flex flex-col md:flex-row items-center gap-6 top-edge-sheen">
        <div className="w-full md:w-56 shrink-0 flex justify-center">
          <HumanAvatar
            state={isSpeakingDebrief ? 'speaking' : 'idle'}
            statusText={isSpeakingDebrief ? 'Interviewer Speaking' : 'Interview Concluded'}
            currentSpeechText={debriefSpeechText}
          />
        </div>
        <div className="flex-1 space-y-3 text-left">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-primary/10 text-primary border border-primary/20">
              Virtual Human Interviewer Debrief
            </span>
            <span className="px-2 py-0.5 bg-secondary/10 text-secondary border border-secondary/30 text-[10px] font-mono font-bold rounded-full">
              Verified FairScore Active
            </span>
          </div>
          <h2 className="text-xl font-bold text-on-surface tracking-tight">
            AI Performance Debrief for {candidateName}
          </h2>
          <p className="text-xs text-on-surface-variant leading-relaxed bg-surface-container p-3.5 rounded-lg border border-outline-variant/30 italic font-mono">
            "{debriefSpeechText}"
          </p>
          <div className="flex flex-wrap items-center gap-3 pt-1">
            <button
              onClick={handleToggleDebriefAudio}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary-container hover:bg-primary-fixed-dim text-on-primary-container text-xs font-mono font-bold rounded-lg shadow-sm transition-all"
            >
              <Volume2 size={15} />
              <span>{isSpeakingDebrief ? 'Stop AI Debrief' : '🔊 Listen to AI Evaluation Debrief'}</span>
            </button>
            <button
              onClick={handleExportJSON}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-surface-container hover:bg-surface-container-high border border-outline-variant/30 text-secondary text-xs font-mono font-semibold rounded-lg transition-colors"
            >
              <Download size={14} />
              <span>Export Audit JSON</span>
            </button>
            <span className="text-[11px] text-outline font-mono">
              Lip-synced speech playback with zero accent bias
            </span>
          </div>
        </div>
      </div>

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
        <div className="bg-surface-container-low border border-outline-variant/30 rounded-xl p-5 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)]">
          <button
            onClick={() => setShowTurnHistory(!showTurnHistory)}
            className="w-full flex items-center justify-between text-left"
          >
            <div className="flex items-center gap-2">
              <MessageSquare size={16} className="text-secondary" />
              <h4 className="text-sm font-bold text-on-surface">
                Turn-by-Turn Transcript & Recovery Deep-Dive ({candidateTurns.length} Responses)
              </h4>
            </div>
            {showTurnHistory ? (
              <ChevronUp size={16} className="text-outline" />
            ) : (
              <ChevronDown size={16} className="text-outline" />
            )}
          </button>

          {showTurnHistory && (
            <div className="mt-4 space-y-3 pt-3 border-t border-outline-variant/20 font-mono text-xs">
              {candidateTurns.map((turn: any, idx: number) => {
                const evalObj = turn.evaluation;
                const sliceLogs = turn.slice_recovery_log || [];

                return (
                  <div
                    key={idx}
                    className="p-3.5 bg-surface-container border border-outline-variant/30 rounded-lg space-y-2"
                  >
                    <div className="flex items-center justify-between text-[11px] font-bold">
                      <span className="text-primary">
                        Turn #{idx + 1} {turn.question_id ? `• ${turn.question_id}` : ''}
                      </span>
                      {evalObj?.scores && (
                        <span className="text-secondary">
                          Score: {evalObj.scores.content_pct}% Content • {evalObj.scores.structure_pct}% Structure
                        </span>
                      )}
                    </div>

                    {turn.question_text && (
                      <div className="text-on-surface font-semibold text-[11px]">
                        Q: {turn.question_text}
                      </div>
                    )}

                    <div className="space-y-1">
                      <div className="text-outline text-[10px] uppercase font-bold">
                        Candidate Answer (Recovered):
                      </div>
                      <p className="text-on-surface-variant leading-relaxed">"{turn.text}"</p>
                    </div>

                    {sliceLogs.length > 0 && (
                      <div className="pt-2 border-t border-outline-variant/20 space-y-1">
                        <span className="text-[10px] uppercase font-bold text-secondary">
                          Acoustic Slice Recoveries (0.0 marks deducted):
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {sliceLogs.map((log: any, lIdx: number) => (
                            <span
                              key={lIdx}
                              className="px-2 py-0.5 bg-surface-container-high border border-secondary/30 rounded text-secondary text-[10px]"
                            >
                              "{log.raw_token || log.original_text || 'has map'}" → {log.verified_token || log.verified_text || 'hash map'}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
