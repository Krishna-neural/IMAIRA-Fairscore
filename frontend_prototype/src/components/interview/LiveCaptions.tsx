import React, { useState } from 'react';
import { Radio, Send, RotateCcw, Mic, MicOff } from 'lucide-react';
import { speechService } from '../../services/speechService';

interface LiveCaptionsProps {
  provisionalText: string;
  finalizedText: string;
  isListening: boolean;
  onSubmitAnswer: (text: string) => void;
  isProcessing: boolean;
  onToggleMic?: () => void;
}

export const LiveCaptions: React.FC<LiveCaptionsProps> = ({
  provisionalText,
  finalizedText,
  isListening,
  onSubmitAnswer,
  isProcessing,
  onToggleMic,
}) => {
  const [typedFallback, setTypedFallback] = useState('');
  const [overrideWithTyped, setOverrideWithTyped] = useState(false);

  const speechText = (finalizedText + ' ' + provisionalText).trim();
  const combined = overrideWithTyped
    ? typedFallback.trim()
    : (typedFallback.trim()
        ? (speechText ? `${speechText} ${typedFallback.trim()}` : typedFallback.trim())
        : speechText);
  const words = combined ? combined.split(/\s+/).filter(Boolean) : [];
  const wordCount = words.length;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!combined) return;
    onSubmitAnswer(combined);
    setTypedFallback('');
  };

  const handleClearAnswer = (e: React.MouseEvent) => {
    e.preventDefault();
    speechService.resetBuffer();
    setTypedFallback('');
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-3.5 shadow-xs space-y-2.5">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 font-bold uppercase text-blue-900 tracking-wider">
            <Radio
              size={14}
              className={isListening ? 'text-emerald-600 animate-pulse' : 'text-slate-400'}
            />
            <span>
              {isListening
                ? 'Continuous Recording Active (No Word Limit)'
                : 'Microphone Standby'}
            </span>
          </div>
          {isListening && (
            <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-bold rounded-full">
              Live Speech Input
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
            {wordCount} words captured
          </span>
          {onToggleMic && (
            <button
              type="button"
              onClick={onToggleMic}
              className={`p-1 rounded text-xs transition-colors ${
                isListening
                  ? 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                  : 'bg-blue-50 hover:bg-blue-100 text-blue-700'
              }`}
              title={isListening ? 'Pause Microphone' : 'Resume Microphone'}
            >
              {isListening ? <Mic size={13} /> : <MicOff size={13} />}
            </button>
          )}
        </div>
      </div>

      {/* Streaming Text Output with Word Counter */}
      <div className="relative min-h-[64px] max-h-40 overflow-y-auto p-3 bg-slate-50 border border-slate-200 rounded text-sm text-slate-800 leading-relaxed font-sans select-text">
        <span className="font-semibold text-[#101C35]">{finalizedText}</span>{' '}
        <span className="text-slate-500 italic">{provisionalText}</span>
        {!finalizedText && !provisionalText && (
          <span className="text-slate-400 italic">
            {isListening
              ? 'Listening continuously... Speak your full technical answer clearly into the microphone. There is no word or time limit.'
              : 'Waiting for prompt...'}
          </span>
        )}
      </div>

      {/* Multi-line Input Drawer, Override Toggle, Clear & Submit Button */}
      <form onSubmit={handleSubmit} className="space-y-2">
        <div className="flex items-start gap-2">
          <textarea
            rows={2}
            value={typedFallback}
            onChange={(e) => setTypedFallback(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                if (combined && !isProcessing) {
                  onSubmitAnswer(combined);
                  setTypedFallback('');
                }
              }
            }}
            placeholder="Type technical answer, formulas, or code here (Ctrl+Enter to submit, no word limit)..."
            className="flex-1 px-3 py-2 text-xs border border-slate-300 rounded text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-600 bg-white resize-y font-sans leading-relaxed"
          />

          <div className="flex flex-col gap-1.5">
            <button
              type="submit"
              disabled={isProcessing || wordCount === 0}
              className="flex items-center justify-center gap-1.5 px-4 py-2 bg-[#2457A6] hover:bg-[#1A4482] text-white rounded text-xs font-semibold shadow-xs disabled:opacity-50 transition-colors shrink-0"
            >
              <Send size={12} />
              {isProcessing ? 'Evaluating...' : `Submit Answer (${wordCount} words)`}
            </button>

            {wordCount > 0 && (
              <button
                type="button"
                onClick={handleClearAnswer}
                disabled={isProcessing}
                title="Clear and re-speak answer"
                className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded text-xs font-medium border border-slate-300 transition-colors"
              >
                <RotateCcw size={12} />
                <span>Clear All</span>
              </button>
            )}
          </div>
        </div>

        {typedFallback.trim() && speechText && (
          <div className="flex items-center gap-2 text-[11px] text-slate-600 pt-0.5">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={overrideWithTyped}
                onChange={(e) => setOverrideWithTyped(e.target.checked)}
                className="rounded text-blue-600 focus:ring-0 cursor-pointer"
              />
              <span>Replace microphone audio with typed text only</span>
            </label>
            <span className="text-slate-400">•</span>
            <span className="text-slate-500 italic">
              {overrideWithTyped ? 'Using typed text' : 'Combining speech + typed text'}
            </span>
          </div>
        )}
      </form>
    </div>
  );
};
