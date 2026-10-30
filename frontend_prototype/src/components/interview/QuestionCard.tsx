import React from 'react';
import { Volume2, BookOpen, Sparkles, HelpCircle } from 'lucide-react';
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
    <div className="bg-white border border-slate-200 border-l-4 border-l-[#2457A6] rounded-xl p-5 shadow-xs font-sans space-y-3">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="px-2.5 py-1 rounded-full text-[11px] font-extrabold uppercase bg-blue-50 text-[#1A4482] border border-blue-200">
            {question?.category || 'Technical Interview Question'}
          </span>
          <span className="px-2.5 py-1 rounded-full text-[11px] font-bold uppercase bg-slate-100 text-slate-700 border border-slate-200">
            {question?.difficulty || 'Intermediate'}
          </span>
          {question?.key_concepts?.map((c, i) => (
            <span
              key={i}
              className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200"
            >
              #{c}
            </span>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-black text-slate-600 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200">
            Question {questionNumber} of {totalQuestions}
          </span>
          {onReplay && (
            <button
              onClick={onReplay}
              className="flex items-center gap-1 px-2.5 py-1 text-xs font-bold text-[#2457A6] bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition-colors"
              title="Hear the interviewer repeat the question"
            >
              <Volume2 size={14} />
              <span>Replay Question</span>
            </button>
          )}
        </div>
      </div>

      <div className="pt-1">
        <h3 className="text-base sm:text-lg font-extrabold text-[#101C35] leading-relaxed">
          {question?.question || 'Preparing your technical question...'}
        </h3>
      </div>

      <div className="text-[11px] text-slate-500 flex items-center gap-1.5 pt-1 border-t border-slate-100">
        <Sparkles size={12} className="text-blue-500" />
        <span>
          Take your time to organize your thoughts. Structure your answer: start with the definition, explain the mechanism, and mention tradeoffs.
        </span>
      </div>
    </div>
  );
};
