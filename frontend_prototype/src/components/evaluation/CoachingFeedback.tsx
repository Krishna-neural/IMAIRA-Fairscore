import React from 'react';
import { Target, ArrowRight } from 'lucide-react';
import { FeedbackItem } from '../../types/evaluation';

interface CoachingFeedbackProps {
  feedback: FeedbackItem[];
}

export const CoachingFeedback: React.FC<CoachingFeedbackProps> = ({ feedback }) => {
  return (
    <div className="bg-surface-container-low border border-outline-variant/30 rounded-xl p-5 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)] space-y-3">
      <div>
        <h3 className="text-sm font-bold text-on-surface">
          Targeted Coaching Recommendations
        </h3>
        <p className="text-xs text-outline font-mono mt-0.5">
          Actionable engineering fixes strictly constrained to ≤ 30 words per recommendation:
        </p>
      </div>

      <div className="space-y-2.5">
        {feedback.length > 0 ? (
          feedback.map((item, idx) => (
            <div
              key={idx}
              className="p-3 bg-surface-container border border-outline-variant/30 rounded-lg text-xs space-y-1.5"
            >
              <div className="flex items-center justify-between text-[11px] font-mono font-bold text-primary uppercase">
                <span>Recommendation #{idx + 1} • {item.dimension}</span>
                <span className="text-error">-{item.marks_lost || 5} marks</span>
              </div>
              {item.quote && (
                <div className="text-outline italic font-mono text-[11px]">
                  "{item.quote}"
                </div>
              )}
              <div className="text-on-surface font-semibold flex items-start gap-1.5 pt-0.5">
                <ArrowRight size={14} className="text-secondary shrink-0 mt-0.5" />
                <span className="leading-relaxed">
                  {((item.fix_sentence || (item as any).model_sentence_fix || '').trim()) ||
                    'Address core algorithm invariants, time/space complexity bounds, and practical edge cases.'}
                </span>
              </div>
            </div>
          ))
        ) : (
          <div className="p-3 bg-surface-container border border-secondary/30 rounded-lg text-xs text-secondary font-mono font-medium">
            Outstanding response! All semantic rubric criteria satisfied with zero coaching deductions.
          </div>
        )}
      </div>
    </div>
  );
};
