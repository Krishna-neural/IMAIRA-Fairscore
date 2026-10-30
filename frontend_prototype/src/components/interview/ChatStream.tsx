import React, { useEffect, useRef } from 'react';
import { UtteranceTurn } from '../../types/interview';

interface ChatStreamProps {
  turns: UtteranceTurn[];
}

export const ChatStream: React.FC<ChatStreamProps> = ({ turns }) => {
  const streamEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    streamEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns]);

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4 h-64 overflow-y-auto space-y-3 shadow-xs">
      {turns.map((turn) => {
        const isAi = turn.speaker === 'ai';
        return (
          <div
            key={turn.id}
            className={`flex flex-col max-w-[85%] rounded-lg p-3 text-sm leading-relaxed ${
              isAi
                ? 'self-start bg-[#EDF3FA] text-[#101C35] border border-[#D0E1F9]'
                : 'self-end bg-white text-slate-800 border border-slate-300 shadow-xs ml-auto'
            }`}
          >
            <div className="flex items-center justify-between text-[11px] font-bold uppercase mb-1">
              <span className={isAi ? 'text-blue-800' : 'text-slate-600'}>
                {isAi ? '🎙️ Virtual Human Interviewer' : '👤 Candidate'}
              </span>
              <span className="text-slate-400 font-mono font-normal">
                {new Date(turn.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>

            <p className="whitespace-pre-wrap">{turn.text}</p>

            {/* Stage 2 Verified Terminology Badges */}
            {turn.auditLog && turn.auditLog.length > 0 && (
              <div className="mt-2 pt-2 border-t border-slate-200 text-xs text-emerald-800 space-y-0.5">
                <span className="font-semibold block">🛡️ Verified Technical Entities:</span>
                <div className="flex flex-wrap gap-1">
                  {turn.auditLog.map((item, idx) => (
                    <span
                      key={idx}
                      className="inline-block px-1.5 py-0.5 bg-emerald-50 border border-emerald-300 rounded font-semibold text-[11px]"
                    >
                      {item.verified_text} <span className="text-slate-400 font-normal">(was '{item.original_text}')</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })}
      <div ref={streamEndRef} />
    </div>
  );
};
