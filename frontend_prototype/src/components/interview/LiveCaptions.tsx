import React, { useState } from 'react';
import { Radio, Send } from 'lucide-react';

interface LiveCaptionsProps {
  provisionalText: string;
  finalizedText: string;
  isListening: boolean;
  onSubmitAnswer: (text: string) => void;
  isProcessing: boolean;
}

export const LiveCaptions: React.FC<LiveCaptionsProps> = ({
  provisionalText,
  finalizedText,
  isListening,
  onSubmitAnswer,
  isProcessing,
}) => {
  const [typedFallback, setTypedFallback] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const candidateAnswer = (finalizedText + ' ' + provisionalText).trim() || typedFallback.trim();
    if (!candidateAnswer) return;
    onSubmitAnswer(candidateAnswer);
    setTypedFallback('');
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-3.5 shadow-xs space-y-2.5">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5 font-bold uppercase text-blue-900 tracking-wider">
          <Radio size={14} className={isListening ? 'text-blue-700 animate-pulse' : 'text-slate-400'} />
          <span>Real-Time Streaming Transcription</span>
        </div>
        <span className="text-[11px] text-slate-400">Sub-second continuous hypothesis updating</span>
      </div>

      {/* Streaming Text Output */}
      <div className="min-h-[52px] p-2.5 bg-slate-50 border border-slate-200 rounded text-sm text-slate-800 leading-relaxed font-sans select-text">
        <span className="font-semibold text-[#101C35]">{finalizedText}</span>{' '}
        <span className="text-slate-500 italic">{provisionalText}</span>
        {!finalizedText && !provisionalText && (
          <span className="text-slate-400 italic">
            {isListening ? 'Speak your answer clearly into the microphone...' : 'Waiting for prompt...'}
          </span>
        )}
      </div>

      {/* Fallback Input Drawer & Submit Button */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={typedFallback}
          onChange={(e) => setTypedFallback(e.target.value)}
          placeholder="Or type technical response here if microphone is noisy..."
          className="flex-1 px-3 py-1.5 text-xs border border-slate-300 rounded text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-600 bg-white"
        />
        <button
          type="submit"
          disabled={isProcessing || (!finalizedText && !provisionalText && !typedFallback.trim())}
          className="flex items-center gap-1.5 px-4 py-1.5 bg-[#2457A6] hover:bg-[#1A4482] text-white rounded text-xs font-semibold shadow-xs disabled:opacity-50 transition-colors"
        >
          <Send size={12} />
          {isProcessing ? 'Evaluating...' : 'Submit Answer'}
        </button>
      </form>
    </div>
  );
};
