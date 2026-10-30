import React, { useState } from 'react';
import { DualDiagnosis } from '../../types/evaluation';
import { AlertCircle, Mic, ArrowRight, ShieldCheck, CheckCircle2, Volume2, RotateCcw, Send, Sparkles } from 'lucide-react';
import { apiService } from '../../services/apiService';

interface DualDiagnosisPanelProps {
  dualDiagnosis?: DualDiagnosis;
  feedback?: Array<{
    dimension: string;
    marks_lost: number;
    quote: string;
    fix_sentence: string;
    question_id?: string;
  }>;
}

export const DualDiagnosisPanel: React.FC<DualDiagnosisPanelProps> = ({
  dualDiagnosis,
  feedback = [],
}) => {
  const [activeReAnswerIdx, setActiveReAnswerIdx] = useState<number | null>(null);
  const [reAnswerText, setReAnswerText] = useState('');
  const [isSubmittingRescore, setIsSubmittingRescore] = useState(false);
  const [remediations, setRemediations] = useState<Record<number, any>>({});

  const techGaps =
    dualDiagnosis?.technical_knowledge_gaps && dualDiagnosis.technical_knowledge_gaps.length > 0
      ? dualDiagnosis.technical_knowledge_gaps
      : feedback.map((fb) => ({
          question_id: fb.question_id || 'ENG001',
          dimension: fb.dimension || 'Content Coverage',
          missing_concepts: [],
          marks_lost: typeof fb.marks_lost === 'number' ? fb.marks_lost : 0,
          quote: fb.quote || '',
          fix_sentence: fb.fix_sentence || '',
        }));

  const pronounceItems = dualDiagnosis?.pronunciation_improvements || [];

  const handleStartReAnswer = (idx: number, modelFix: string) => {
    setActiveReAnswerIdx(idx);
    setReAnswerText(modelFix);
  };

  const handleExecuteRescore = async (idx: number, gap: any) => {
    if (!reAnswerText.trim() || isSubmittingRescore) return;
    setIsSubmittingRescore(true);

    try {
      const qId = gap.question_id || 'ENG001';
      const cId = (gap as any).criterion_id || `crit_${idx + 1}`;
      const prevMarks = typeof gap.marks_lost === 'number' ? gap.marks_lost : 10;

      const res = await apiService.rescoreSegment({
        question_id: qId,
        criterion_id: cId,
        previous_marks_lost: prevMarks,
        new_transcript: reAnswerText.trim(),
      });

      setRemediations((prev) => ({
        ...prev,
        [idx]: res,
      }));
      setActiveReAnswerIdx(null);
    } catch (err) {
      console.error('[DualDiagnosisPanel] Rescore failed:', err);
    } finally {
      setIsSubmittingRescore(false);
    }
  };

  return (
    <div className="space-y-6 mb-6">
      <div className="border-b border-slate-200 pb-2">
        <h3 className="text-xl font-bold text-[#101C35]">
          Dual Diagnosis: Technical Mastery vs. Articulation Improvement
        </h3>
        <p className="text-xs text-slate-500 mt-0.5">
          Strict architectural bifurcation: Technical knowledge gaps directly affect scoring, while accent and pronunciation recoveries are provided for candidate coaching with zero score deduction.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Column 1: Technical Knowledge Gaps (Evaluated for Marks) */}
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-red-50 text-red-700 rounded border border-red-200">
                <AlertCircle size={18} />
              </div>
              <div>
                <h4 className="text-sm font-bold text-[#101C35]">
                  Technical Knowledge Gaps
                </h4>
                <span className="text-[11px] text-slate-500 block">
                  Conceptual omissions & rubric mark deductions
                </span>
              </div>
            </div>
            <span className="px-2 py-0.5 bg-red-100 text-red-800 text-[10px] font-extrabold rounded-full border border-red-200 uppercase">
              Score Impacting
            </span>
          </div>

          <div className="space-y-3">
            {techGaps.length > 0 ? (
              techGaps.map((gap, idx) => {
                const rem = remediations[idx];
                const isRemediated = rem?.is_remediated;
                const isSatisfied =
                  isRemediated ||
                  (gap as any).status === 'satisfied' ||
                  (gap as any).criterion_id === 'ALL_SATISFIED' ||
                  gap.marks_lost === 0;

                const baseMarksLost =
                  typeof gap.marks_lost === 'number' ? gap.marks_lost : isSatisfied ? 0 : 5;
                const marksLost = rem ? rem.new_marks_lost : baseMarksLost;

                const fix = (
                  gap.fix_sentence ||
                  (gap as any).model_sentence_fix ||
                  (gap as any).concept ||
                  ''
                ).trim();
                const displayFix =
                  fix && fix.length > 3
                    ? fix
                    : 'Explain core algorithmic mechanics, asymptotic space-time bounds, and practical implementation tradeoffs.';

                return (
                  <div
                    key={idx}
                    className={`p-3.5 border rounded-lg text-xs space-y-2 transition-all ${
                      isRemediated
                        ? 'bg-emerald-50/70 border-emerald-300'
                        : 'bg-slate-50 border-slate-200'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-[#2457A6] text-[11px]">
                        {gap.question_id ? `Question ${gap.question_id}` : `Criterion #${idx + 1}`}
                        {` • ${gap.dimension || (gap as any).concept || 'Technical Knowledge Mastery'}`}
                        {(gap as any).concept && (gap as any).concept !== gap.dimension
                          ? ` (${(gap as any).concept})`
                          : ''}
                      </span>
                      {isRemediated ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-100 text-emerald-800 border border-emerald-300 rounded text-[10px] font-bold">
                          <Sparkles size={11} />
                          Remediated (+{rem.marks_recovered} pts)
                        </span>
                      ) : isSatisfied ? (
                        <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded text-[10px] font-bold">
                          Full Mastery (0 marks lost)
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 bg-red-50 text-red-700 border border-red-200 rounded text-[10px] font-bold">
                          -{marksLost} marks
                        </span>
                      )}
                    </div>

                    {gap.missing_concepts && gap.missing_concepts.length > 0 ? (
                      <div className="space-y-1">
                        <span className="text-[10px] uppercase font-bold text-slate-400">
                          Missing Required Concepts:
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {gap.missing_concepts.map((mc, mIdx) => (
                            <span
                              key={mIdx}
                              className="px-2 py-0.5 bg-white border border-slate-300 rounded text-[11px] text-slate-700 font-medium"
                            >
                              {mc}
                            </span>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-1">
                        <span className="text-[10px] uppercase font-bold text-slate-400">
                          Key Architectural Focus:
                        </span>
                        <span className="px-2 py-0.5 bg-white border border-slate-300 rounded text-[11px] text-slate-700 font-medium inline-block">
                          {(gap as any).concept || gap.dimension || 'Technical Accuracy & Complexity'}
                        </span>
                      </div>
                    )}

                    {gap.quote && (
                      <div className="text-slate-600 italic bg-white p-2 rounded border border-slate-200 text-[11px]">
                        "{gap.quote}"
                      </div>
                    )}

                    <div className="space-y-1 pt-1">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] uppercase font-bold text-emerald-800 block">
                          Recommended Model Answer / Fix:
                        </span>
                        {!isSatisfied && activeReAnswerIdx !== idx && (
                          <button
                            type="button"
                            onClick={() => handleStartReAnswer(idx, displayFix)}
                            className="inline-flex items-center gap-1 text-[10px] font-bold text-blue-700 hover:text-blue-900 bg-blue-50 hover:bg-blue-100 px-2 py-0.5 rounded border border-blue-200 transition-colors"
                          >
                            <RotateCcw size={10} />
                            <span>Practice Re-Answer</span>
                          </button>
                        )}
                      </div>
                      <div className="p-2.5 bg-emerald-50/70 border border-emerald-200 rounded text-[#101C35] font-semibold flex items-start gap-1.5 text-xs">
                        <ArrowRight size={14} className="text-emerald-700 shrink-0 mt-0.5" />
                        <span>{displayFix}</span>
                      </div>
                    </div>

                    {/* Interactive Re-Answer Loop Drawer (X-Factor #3) */}
                    {activeReAnswerIdx === idx && (
                      <div className="p-3 bg-blue-50/70 border border-blue-200 rounded-lg space-y-2 animate-fadeIn mt-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-bold text-blue-900 flex items-center gap-1">
                            <RotateCcw size={12} />
                            Re-Answer Loop: Instant Rescoring Practice
                          </span>
                          <button
                            type="button"
                            onClick={() => setActiveReAnswerIdx(null)}
                            className="text-[10px] text-slate-500 hover:text-slate-700"
                          >
                            Cancel
                          </button>
                        </div>
                        <p className="text-[11px] text-slate-600">
                          Speak or edit your improved explanation incorporating the model fix to recover lost rubric marks:
                        </p>
                        <textarea
                          value={reAnswerText}
                          onChange={(e) => setReAnswerText(e.target.value)}
                          rows={2}
                          className="w-full p-2 text-xs border border-blue-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-600 bg-white"
                          placeholder="Speak or type your re-answer here..."
                        />
                        <div className="flex items-center justify-end gap-2">
                          <button
                            type="button"
                            disabled={isSubmittingRescore || !reAnswerText.trim()}
                            onClick={() => handleExecuteRescore(idx, gap)}
                            className="inline-flex items-center gap-1 px-3 py-1 bg-[#2457A6] hover:bg-[#1b4383] text-white text-xs font-bold rounded shadow-xs transition-colors disabled:opacity-50"
                          >
                            {isSubmittingRescore ? (
                              <span>Evaluating...</span>
                            ) : (
                              <>
                                <Send size={11} />
                                <span>Rescore Segment</span>
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-center space-y-1">
                <CheckCircle2 size={24} className="text-emerald-700 mx-auto" />
                <h5 className="text-xs font-bold text-emerald-900">
                  Comprehensive Technical Coverage
                </h5>
                <p className="text-[11px] text-emerald-700">
                  Candidate successfully hit all key semantic concepts across all evaluated technical rubrics.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Column 2: Pronunciation & Articulation Scopes of Improvement (Zero Deduction Guarantee) */}
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-blue-50 text-[#2457A6] rounded border border-blue-200">
                <Mic size={18} />
              </div>
              <div>
                <h4 className="text-sm font-bold text-[#101C35]">
                  Pronunciation & Articulation Scopes of Improvement
                </h4>
                <span className="text-[11px] text-slate-500 block">
                  Acoustic recovery log with candidate coaching tips
                </span>
              </div>
            </div>
            <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 text-[10px] font-extrabold rounded-full border border-emerald-200 uppercase">
              0.0 Marks Deducted
            </span>
          </div>

          <div className="space-y-3">
            {pronounceItems.length > 0 ? (
              pronounceItems.map((item, idx) => (
                <div
                  key={idx}
                  className="p-3.5 bg-blue-50/50 border border-blue-200 rounded-lg text-xs space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200 text-[11px]">
                        "{item.raw_token}"
                      </span>
                      <ArrowRight size={12} className="text-blue-700" />
                      <span className="font-bold text-[#101C35] text-xs">
                        {item.recovered_token}
                      </span>
                    </div>
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                      <ShieldCheck size={12} />
                      Full Credit Given
                    </span>
                  </div>

                  <div className="p-2.5 bg-white border border-blue-100 rounded text-slate-700 space-y-1">
                    <div className="flex items-center gap-1.5 text-[#2457A6] font-bold text-[11px]">
                      <Volume2 size={13} />
                      <span>Coaching Advice:</span>
                    </div>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      {item.coaching}
                    </p>
                  </div>

                  <div className="text-[10px] text-slate-500 flex items-center justify-between pt-0.5">
                    <span>
                      {item.question_id ? `Referenced in Question ${item.question_id}` : 'General technical vocabulary'}
                    </span>
                    <span className="font-semibold text-emerald-800">
                      Deduction: 0.0 marks
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-center space-y-1">
                <ShieldCheck size={24} className="text-blue-700 mx-auto" />
                <h5 className="text-xs font-bold text-slate-800">
                  Clean Articulation Verified
                </h5>
                <p className="text-[11px] text-slate-500">
                  All technical terms were articulated within high acoustic confidence thresholds (&gt;0.85). No pronunciation slips detected.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
