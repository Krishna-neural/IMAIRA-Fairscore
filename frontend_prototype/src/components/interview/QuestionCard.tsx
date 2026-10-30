import React from 'react';
import { Volume2, BookOpen } from 'lucide-react';
import { Question } from '../../types/interview';

interface QuestionCardProps {
  question: Question | null;
  questionNumber: number;
  totalQuestions: number;
  onReplay?: () => void;
}

export const QuestionCard: React.FC<QuestionCardProps> = ({
  question,
  questionNumber,
  totalQuestions,
  onReplay,
}) => {
  return (
    <div className="w-full rounded-2xl bg-surface-container/70 border border-outline-variant/30 backdrop-blur-xl shadow-[0_8px_30px_rgba(0,0,0,0.65)] p-5 relative overflow-hidden">
      {/* Top light refraction gradient line */}
      <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent"></div>

      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-primary/10 text-primary border border-primary/25">
            {question?.category || 'Engineering Question'}
          </span>
          <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-surface-container-high text-on-surface-variant border border-outline-variant/30">
            {question?.difficulty || 'Intermediate'}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-outline">
            Question <span className="text-primary font-bold">{questionNumber}</span> of {totalQuestions}
          </span>
          {onReplay && (
            <button
              onClick={onReplay}
              className="p-1 rounded bg-surface-container text-on-surface-variant hover:text-secondary hover:bg-surface-container-high transition-colors"
              title="Replay Spoken Question"
            >
              <Volume2 size={15} />
            </button>
          )}
        </div>
      </div>

      <p className="text-base sm:text-lg font-medium text-on-surface leading-snug">
        “{question?.question || 'Preparing your technical question...'}”
      </p>

      {question?.key_concepts && question.key_concepts.length > 0 && (
        <div className="mt-3.5 flex flex-wrap items-center gap-2 text-xs font-mono">
          <span className="text-outline text-[11px]">Technical Focus:</span>
          {question.key_concepts.map((c, i) => (
            <span
              key={i}
              className="px-2.5 py-0.5 rounded bg-surface-container-high text-secondary border border-secondary/20 text-[11px]"
            >
              {c}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
