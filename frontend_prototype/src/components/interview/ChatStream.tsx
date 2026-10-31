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
    <div className="bg-surface-container-low border border-outline-variant/30 rounded-xl p-4 h-64 overflow-y-auto space-y-3 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)]">
      {turns.map((turn) => {
        const isAi = turn.speaker === 'ai';
        return (
          <div
            key={turn.id}
            className={`flex flex-col max-w-[85%] rounded-xl p-3.5 text-xs leading-relaxed ${
              isAi
                ? 'self-start bg-surface-container text-on-surface border border-outline-variant/30'
                : 'self-end bg-surface-container-high text-on-surface border border-primary/40 shadow-sm ml-auto'
            }`}
          >
            <div className="flex items-center justify-between text-[11px] font-mono font-bold uppercase mb-1.5">
              <span className={isAi ? 'text-primary flex items-center gap-1' : 'text-secondary flex items-center gap-1'}>
                <span className="material-symbols-outlined" style={{ fontSize: '13px' }}>
                  {isAi ? 'smart_toy' : 'person'}
                </span>
                <span>{isAi ? 'Virtual Human Interviewer' : 'Candidate'}</span>
              </span>
              <span className="text-outline font-mono text-[10px]">
                {new Date(turn.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </span>
            </div>

            <p className="whitespace-pre-wrap">{turn.text}</p>

            {/* Stage 2 Verified Terminology Badges */}
            {turn.auditLog && turn.auditLog.length > 0 && (
              <div className="mt-2.5 pt-2 border-t border-outline-variant/20 text-xs font-mono text-secondary space-y-1">
                <span className="font-semibold block text-[10px] text-outline uppercase tracking-wider">
                  🛡️ Acoustically Verified Entities:
                </span>
                <div className="flex flex-wrap gap-1">
                  {turn.auditLog.map((item, idx) => (
                    <span
                      key={idx}
                      className="inline-block px-2 py-0.5 bg-surface-container-lowest border border-secondary/30 rounded font-semibold text-[11px] text-secondary"
                    >
                      {item.verified_text} <span className="text-outline font-normal">(was '{item.original_text}')</span>
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
