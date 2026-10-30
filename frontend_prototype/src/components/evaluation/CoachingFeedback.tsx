import React from 'react';
import { Target, ArrowRight } from 'lucide-react';
import { FeedbackItem } from '../../types/evaluation';

interface CoachingFeedbackProps {
  feedback: FeedbackItem[];
}

export const CoachingFeedback: React.FC<CoachingFeedbackProps> = ({ feedback }) => {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
      <h3 className="text-base font-bold text-[#101C35] mb-1">
        Targeted Coaching Recommendations
      </h3>
      <p className="text-xs text-slate-500 mb-3.5">
        Actionable coaching fixes strictly constrained to ≤ 30 words per recommendation:
      </p>

      <div className="space-y-2.5">
        {feedback.length > 0 ? (
          feedback.map((item, idx) => (
            <div
              key={idx}
              className="p-3 bg-[#EDF3FA] border border-[#D0E1F9] rounded text-xs space-y-1"
            >
              <div className="flex items-center justify-between text-[11px] font-bold text-[#2457A6] uppercase">
                <span>Recommendation #{idx + 1} • {item.dimension}</span>
                <span>-{item.marks_lost || 5} marks</span>
              </div>
              {item.quote && (
                <div className="text-slate-600 italic">
                  "{item.quote}"
                </div>
              )}
              <div className="text-[#101C35] font-semibold flex items-start gap-1 pt-0.5">
                <ArrowRight size={14} className="text-[#2457A6] shrink-0 mt-0.5" />
                <span>
                  {((item.fix_sentence || (item as any).model_sentence_fix || '').trim()) ||
                    'Address core algorithm invariants, time/space complexity bounds, and practical edge cases.'}
                </span>
              </div>
            </div>
          ))
        ) : (
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded text-xs text-emerald-800 font-medium">
            Outstanding response! All semantic rubric criteria satisfied with zero coaching deductions.
          </div>
        )}
      </div>
    </div>
  );
};
