import React, { useState } from 'react';
import { DualDiagnosis } from '../../types/evaluation';
import { AlertCircle, Mic, ArrowRight, ShieldCheck, CheckCircle2, Volume2, RotateCcw, Send, Sparkles, Award } from 'lucide-react';
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
    <div className="space-y-6 mb-6 font-sans">
      <div className="border-b border-slate-200 pb-3">
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-[#2457A6] text-white">
            Core Fairness Bifurcation
          </span>
          <span className="text-xs text-slate-500 font-medium">
            Strict Separation of Knowledge vs. Articulation
          </span>
        </div>
        <h3 className="text-xl font-extrabold text-[#101C35] mt-1.5">
          Dual Diagnosis: Technical Knowledge vs. Articulation Coaching
        </h3>
        <p className="text-xs text-slate-600 mt-1 max-w-3xl leading-relaxed">
          In campus placement interviews, students often score low because generic tools blend accent into content. IMAIRA FairScore guarantees that <strong>technical gaps affect marks</strong>, while <strong>pronunciation improvements carry 0.0 marks deducted</strong>.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        {/* Column 1: Technical Knowledge Gaps (Affects Score) */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2.5">
              <div className="p-2 bg-red-50 text-red-700 rounded-lg border border-red-200">
                <AlertCircle size={18} />
              </div>
              <div>
                <h4 className="text-sm font-black text-[#101C35]">
                  Technical Knowledge Gaps
                </h4>
                <span className="text-[11px] text-slate-500 block">
                  Conceptual omissions & rubric marks deducted
                </span>
              </div>
            </div>
            <span className="px-2.5 py-1 bg-red-100 text-red-800 text-[10px] font-black rounded-full border border-red-200 uppercase">
              Score Impacting
            </span>
          </div>

          <div className="space-y-3.5">
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
                    className={`p-4 border rounded-xl text-xs space-y-2.5 transition-all ${
                      isRemediated
                        ? 'bg-emerald-50/70 border-emerald-300 ring-2 ring-emerald-500/20'
                        : 'bg-slate-50 border-slate-200'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-extrabold text-[#2457A6] text-xs">
                        {gap.question_id ? `Question ${gap.question_id}` : `Criterion #${idx + 1}`}
                        {` • ${gap.dimension || (gap as any).concept || 'Technical Mastery'}`}
                      </span>
                      {isRemediated ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-emerald-100 text-emerald-800 border border-emerald-300 rounded-full text-[10px] font-bold">
                          <Sparkles size={11} />
                          Remediated (+{rem.marks_recovered} pts)
                        </span>
                      ) : isSatisfied ? (
                        <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full text-[10px] font-bold">
                          Full Mastery (0 marks lost)
                        </span>
                      ) : (
                        <span className="px-2.5 py-0.5 bg-red-100 text-red-700 border border-red-200 rounded-full text-[10px] font-black">
                          -{marksLost} marks
                        </span>
                      )}
                    </div>

                    {gap.missing_concepts && gap.missing_concepts.length > 0 ? (
                      <div className="space-y-1">
                        <span className="text-[10px] uppercase font-bold text-slate-500">
                          Missing Conceptual Rubrics:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {gap.missing_concepts.map((mc, mIdx) => (
                            <span
                              key={mIdx}
                              className="px-2.5 py-0.5 bg-white border border-slate-300 rounded-md text-[11px] text-slate-700 font-semibold"
                            >
                              {mc}
                            </span>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-1">
                        <span className="text-[10px] uppercase font-bold text-slate-500">
                          Target Competence:
                        </span>
                        <span className="px-2.5 py-0.5 bg-white border border-slate-300 rounded-md text-[11px] text-slate-800 font-semibold inline-block">
                          {(gap as any).concept || gap.dimension || 'Technical Accuracy & Tradeoffs'}
                        </span>
                      </div>
                    )}

                    {gap.quote && (
                      <div className="text-slate-600 italic bg-white p-2.5 rounded-lg border border-slate-200 text-[11px]">
                        "{gap.quote}"
                      </div>
                    )}

                    {/* Model Sentence Fix (≤30 words) */}
                    <div className="space-y-1.5 pt-1">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] uppercase font-bold text-emerald-800 block">
                          Model Answer / Actionable Fix (≤30 words):
                        </span>
                        {!isSatisfied && activeReAnswerIdx !== idx && (
                          <button
                            type="button"
                            onClick={() => handleStartReAnswer(idx, displayFix)}
                            className="inline-flex items-center gap-1 text-[11px] font-bold text-[#2457A6] hover:text-[#1A4482] bg-blue-50 hover:bg-blue-100 px-2.5 py-1 rounded-lg border border-blue-200 transition-all shadow-xs"
                          >
                            <RotateCcw size={11} />
                            <span>Practice Re-Answer</span>
                          </button>
                        )}
                      </div>
                      <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-950 font-medium flex items-start gap-2 text-xs leading-relaxed">
                        <ArrowRight size={15} className="text-emerald-700 shrink-0 mt-0.5" />
                        <span>{displayFix}</span>
                      </div>
                    </div>

                    {/* Interactive Re-Answer Loop Drawer (X-Factor #3) */}
                    {activeReAnswerIdx === idx && (
                      <div className="p-3.5 bg-blue-50/80 border-2 border-blue-300 rounded-xl space-y-2.5 animate-fadeIn mt-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-bold text-blue-950 flex items-center gap-1.5">
                            <RotateCcw size={13} className="text-[#2457A6]" />
                            Re-Answer Practice: Recover Lost Marks Now
                          </span>
                          <button
                            type="button"
                            onClick={() => setActiveReAnswerIdx(null)}
                            className="text-[11px] text-slate-500 hover:text-slate-700 font-semibold"
                          >
                            Cancel
                          </button>
                        </div>
                        <p className="text-[11px] text-slate-600">
                          Re-speak or refine your explanation using the model fix below. The engine will instantly rescore this rubric criterion:
                        </p>
                        <textarea
                          value={reAnswerText}
                          onChange={(e) => setReAnswerText(e.target.value)}
                          rows={2}
                          className="w-full p-2.5 text-xs border border-blue-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 bg-white"
                          placeholder="Speak or type your improved answer here..."
                        />
                        <div className="flex items-center justify-end gap-2">
                          <button
                            type="button"
                            disabled={isSubmittingRescore || !reAnswerText.trim()}
                            onClick={() => handleExecuteRescore(idx, gap)}
                            className="inline-flex items-center gap-1.5 px-4 py-1.5 bg-[#2457A6] hover:bg-[#1A4482] text-white text-xs font-bold rounded-lg shadow-xs transition-all disabled:opacity-50"
                          >
                            {isSubmittingRescore ? (
                              <span>Evaluating Improvements...</span>
                            ) : (
                              <>
                                <Send size={12} />
                                <span>Rescore Segment Now</span>
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
              <div className="p-6 bg-emerald-50 border border-emerald-200 rounded-xl text-center space-y-2">
                <CheckCircle2 size={28} className="text-emerald-700 mx-auto" />
                <h5 className="text-sm font-bold text-emerald-900">
                  Comprehensive Technical Coverage
                </h5>
                <p className="text-xs text-emerald-700">
                  Candidate successfully articulated all key algorithmic mechanisms and asymptotic bounds with zero mark deductions.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Column 2: Pronunciation & Articulation Scopes of Improvement (0.0 Marks Deducted) */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2.5">
              <div className="p-2 bg-emerald-50 text-emerald-700 rounded-lg border border-emerald-200">
                <Mic size={18} />
              </div>
              <div>
                <h4 className="text-sm font-black text-[#101C35]">
                  Pronunciation & Delivery Coaching
                </h4>
                <span className="text-[11px] text-slate-500 block">
                  Acoustic recovery log with candidate delivery tips
                </span>
              </div>
            </div>
            <span className="px-2.5 py-1 bg-emerald-100 text-emerald-800 text-[10px] font-black rounded-full border border-emerald-200 uppercase">
              0.0 Marks Deducted
            </span>
          </div>

          <div className="space-y-3.5">
            {pronounceItems.length > 0 ? (
              pronounceItems.map((item, idx) => (
                <div
                  key={idx}
                  className="p-4 bg-blue-50/40 border border-blue-200 rounded-xl text-xs space-y-2.5"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200 text-[11px]">
                        "{item.raw_token}"
                      </span>
                      <ArrowRight size={13} className="text-[#2457A6]" />
                      <span className="font-bold text-[#101C35] text-xs">
                        {item.recovered_token}
                      </span>
                    </div>
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                      <ShieldCheck size={13} className="text-emerald-600" />
                      Full Credit Given
                    </span>
                  </div>

                  <div className="p-3 bg-white border border-blue-100 rounded-lg text-slate-700 space-y-1">
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
                    <span className="font-bold text-emerald-800">
                      Deduction: 0.0 marks (Zero Penalty)
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-6 bg-slate-50 border border-slate-200 rounded-xl text-center space-y-2">
                <ShieldCheck size={28} className="text-[#2457A6] mx-auto" />
                <h5 className="text-sm font-bold text-slate-800">
                  Clean Articulation Verified
                </h5>
                <p className="text-xs text-slate-500">
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
