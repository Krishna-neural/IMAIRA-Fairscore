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
    <div className="bg-white border border-slate-200 border-l-4 border-l-[#2457A6] rounded-lg p-4 shadow-xs">
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase bg-blue-50 text-blue-800 border border-blue-200">
            {question?.category || 'Engineering Question'}
          </span>
          <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase bg-slate-100 text-slate-700 border border-slate-200">
            {question?.difficulty || 'Intermediate'}
          </span>
          {question?.key_concepts?.map((c, i) => (
            <span
              key={i}
              className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-50 text-slate-600 border border-slate-200"
            >
              {c}
            </span>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-500">
            Question {questionNumber} of {totalQuestions}
          </span>
          {onReplay && (
            <button
              onClick={onReplay}
              className="p-1 text-slate-400 hover:text-blue-700 transition-colors"
              title="Replay Spoken Question"
            >
              <Volume2 size={16} />
            </button>
          )}
        </div>
      </div>

      <h3 className="text-base font-bold text-[#101C35] leading-snug">
        {question?.question || 'Preparing your technical question...'}
      </h3>
    </div>
  );
};
