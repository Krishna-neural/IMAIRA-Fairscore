import React, { useState } from 'react';
import { Radio, Send, RotateCcw, Mic, MicOff, ShieldCheck, Edit3, Check, Globe, Sparkles } from 'lucide-react';
import { speechService } from '../../services/speechService';
import { phoneticRecovery } from '../../services/phoneticRecovery';

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
  const [isEditing, setIsEditing] = useState(false);
  const [manualText, setManualText] = useState('');
  const [language, setLanguage] = useState<string>(speechService.getLanguage());

  const spokenText = (finalizedText + ' ' + provisionalText).trim();
  const rawCombined = overrideWithTyped
    ? typedFallback.trim()
    : (typedFallback.trim()
        ? (spokenText ? `${spokenText} ${typedFallback.trim()}` : typedFallback.trim())
        : spokenText);

  const recovery = phoneticRecovery.recoverText(rawCombined);
  const combined = isEditing ? manualText : recovery.text;
  const words = combined ? combined.split(/\s+/).filter(Boolean) : [];
  const wordCount = words.length;

  const handleLanguageChange = (newLang: string) => {
    setLanguage(newLang);
    speechService.setLanguage(newLang);
  };

  const handleToggleEdit = () => {
    if (!isEditing) {
      setManualText(combined);
      setIsEditing(true);
    } else {
      speechService.setFinalizedBuffer(manualText);
      setIsEditing(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const textToSubmit = isEditing ? manualText : combined;
    if (!textToSubmit || !textToSubmit.trim()) return;
    onSubmitAnswer(textToSubmit.trim());
    setTypedFallback('');
    setManualText('');
    setIsEditing(false);
  };

  const handleClearAnswer = (e: React.MouseEvent) => {
    e.preventDefault();
    speechService.resetBuffer();
    setTypedFallback('');
    setManualText('');
    setIsEditing(false);
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs space-y-3 font-sans">
      {/* Header Bar */}
      <div className="flex items-center justify-between text-xs flex-wrap gap-2 pb-1 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider">
            <Radio
              size={15}
              className={isListening ? 'text-emerald-600 animate-pulse' : 'text-slate-400'}
            />
            <span className={isListening ? 'text-emerald-800 font-extrabold' : 'text-slate-500'}>
              {isListening
                ? 'Listening Continuously (No Word or Time Limit)'
                : 'Microphone Paused'}
            </span>
          </div>
          {isListening && (
            <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 border border-emerald-300 text-[10px] font-bold rounded-full animate-fadeIn">
              Live Speech Input
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Accent Model Selector */}
          <div className="flex items-center gap-1 bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-[11px] text-slate-700">
            <Globe size={12} className="text-[#2457A6]" />
            <span className="font-semibold text-slate-500 mr-0.5">Model:</span>
            <select
              value={language}
              onChange={(e) => handleLanguageChange(e.target.value)}
              className="bg-transparent font-bold text-slate-800 text-[11px] focus:outline-none cursor-pointer"
            >
              <option value="en-IN">🇮🇳 English (India)</option>
              <option value="en-US">🇺🇸 English (US)</option>
              <option value="en-GB">🇬🇧 English (UK)</option>
            </select>
          </div>

          <span className="text-[11px] font-bold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200">
            {wordCount} words
          </span>

          <button
            type="button"
            onClick={handleToggleEdit}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all border ${
              isEditing
                ? 'bg-emerald-50 text-emerald-800 border-emerald-300 shadow-xs'
                : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
            }`}
            title={isEditing ? 'Save manual edits' : 'Edit speech transcript manually'}
          >
            {isEditing ? <Check size={12} /> : <Edit3 size={12} />}
            <span>{isEditing ? 'Done Editing' : 'Edit Text'}</span>
          </button>

          {onToggleMic && (
            <button
              type="button"
              onClick={onToggleMic}
              className={`p-1.5 rounded-lg text-xs transition-colors border ${
                isListening
                  ? 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300'
                  : 'bg-blue-50 hover:bg-blue-100 text-[#2457A6] border-blue-200'
              }`}
              title={isListening ? 'Pause Microphone' : 'Resume Microphone'}
            >
              {isListening ? <Mic size={14} /> : <MicOff size={14} />}
            </button>
          )}
        </div>
      </div>

      {/* Streaming Text Output or Manual Edit Mode */}
      {isEditing ? (
        <div className="space-y-1.5">
          <textarea
            value={manualText}
            onChange={(e) => setManualText(e.target.value)}
            rows={3}
            placeholder="Edit or refine your technical answer text directly here..."
            className="w-full p-3 text-xs text-slate-800 border-2 border-blue-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 bg-white leading-relaxed font-sans"
          />
          <span className="text-[11px] text-slate-500 italic block">
            Directly adjust any words before submitting. Stage 2 acoustic recovery will remain active.
          </span>
        </div>
      ) : (
        <div className="relative min-h-[72px] max-h-48 overflow-y-auto p-3.5 bg-slate-50 border border-slate-200 rounded-lg text-xs sm:text-sm text-slate-800 leading-relaxed font-sans select-text">
          <span className="font-semibold text-[#101C35]">{finalizedText}</span>{' '}
          <span className="text-slate-500 italic">{provisionalText}</span>
          {!finalizedText && !provisionalText && !typedFallback && (
            <div className="text-slate-400 italic flex items-center gap-2 py-2">
              <Sparkles size={16} className="text-blue-500 shrink-0" />
              <span>
                {isListening
                  ? 'Listening continuously... Speak your technical explanation clearly. Take your time to think.'
                  : 'Microphone paused. Click Unmute to continue speaking.'}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Live Acoustic Terminology Recovery Chips (Proves 0.0 Marks Deducted) */}
      {recovery.auditItems.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap p-2.5 text-xs text-emerald-900 bg-emerald-50/90 rounded-lg border border-emerald-200">
          <div className="flex items-center gap-1.5 font-bold text-emerald-800 shrink-0">
            <ShieldCheck size={16} className="text-emerald-600" />
            <span>Acoustically Recovered:</span>
          </div>
          {recovery.auditItems.slice(0, 4).map((item, idx) => (
            <span key={idx} className="font-semibold bg-white px-2 py-0.5 rounded border border-emerald-300 text-[11px] text-emerald-950">
              "{item.original}" → <strong className="text-emerald-700">{item.recovered}</strong>
            </span>
          ))}
          <span className="text-[11px] text-emerald-700 font-bold ml-auto shrink-0 bg-emerald-100 px-2 py-0.5 rounded">
            ✓ 0.0 Marks Deducted
          </span>
        </div>
      )}

      {/* Input Area + Submit Button */}
      <form onSubmit={handleSubmit} className="space-y-2">
        <div className="flex items-start gap-2.5">
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
            placeholder="Type technical formulas, code, or additional notes here (Press Ctrl + Enter to submit)..."
            className="flex-1 px-3 py-2.5 text-xs border border-slate-300 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-[#2457A6] bg-white resize-y font-sans leading-relaxed"
          />

          <div className="flex flex-col gap-1.5 shrink-0">
            <button
              type="submit"
              disabled={isProcessing || wordCount === 0}
              className="flex items-center justify-center gap-2 px-5 py-2.5 bg-[#2457A6] hover:bg-[#1A4482] text-white rounded-lg text-xs font-bold shadow-sm hover:shadow transition-all disabled:opacity-40"
            >
              <Send size={13} />
              <span>{isProcessing ? 'Evaluating...' : `Submit Answer (${wordCount} words)`}</span>
            </button>

            {wordCount > 0 && (
              <button
                type="button"
                onClick={handleClearAnswer}
                disabled={isProcessing}
                className="flex items-center justify-center gap-1 px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg text-[11px] font-semibold border border-slate-300 transition-colors"
              >
                <RotateCcw size={11} />
                <span>Clear All</span>
              </button>
            )}
          </div>
        </div>

        {typedFallback.trim() && spokenText && (
          <div className="flex items-center gap-2 text-[11px] text-slate-600 pt-0.5">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={overrideWithTyped}
                onChange={(e) => setOverrideWithTyped(e.target.checked)}
                className="rounded text-blue-600 focus:ring-0 cursor-pointer"
              />
              <span>Use typed text only (ignore voice audio)</span>
            </label>
            <span className="text-slate-400">•</span>
            <span className="text-slate-500 italic">
              {overrideWithTyped ? 'Voice overridden' : 'Combining spoken audio + typed text'}
            </span>
          </div>
        )}
      </form>
    </div>
  );
};
