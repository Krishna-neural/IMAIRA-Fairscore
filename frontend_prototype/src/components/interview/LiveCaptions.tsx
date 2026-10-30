import React, { useState } from 'react';
import { Radio, Send, RotateCcw, Mic, MicOff, ShieldCheck, Edit3, Check, Globe } from 'lucide-react';
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
    <div className="bg-surface-container-low border border-outline-variant/30 rounded-xl p-4 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)] space-y-3">
      <div className="flex items-center justify-between text-xs flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 font-mono font-bold uppercase text-secondary tracking-wider">
            <Radio
              size={14}
              className={isListening ? 'text-secondary animate-pulse' : 'text-outline'}
            />
            <span>
              {isListening
                ? 'Continuous Recording Active (No Word Limit)'
                : 'Microphone Standby'}
            </span>
          </div>
          {isListening && (
            <span className="px-2 py-0.5 bg-secondary/15 text-secondary border border-secondary/30 text-[10px] font-mono font-bold rounded-full">
              Live Speech Input
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Acoustic Profile / Accent Selector */}
          <div className="flex items-center gap-1 bg-surface-container border border-outline-variant/30 rounded-lg px-2.5 py-1 text-[11px] text-on-surface">
            <Globe size={12} className="text-secondary" />
            <span className="font-mono text-outline mr-0.5">Model:</span>
            <select
              value={language}
              onChange={(e) => handleLanguageChange(e.target.value)}
              className="bg-transparent font-mono font-bold text-on-surface text-[11px] focus:outline-none cursor-pointer"
            >
              <option value="en-IN" className="bg-surface text-on-surface">🇮🇳 English (India)</option>
              <option value="en-US" className="bg-surface text-on-surface">🇺🇸 English (US)</option>
              <option value="en-GB" className="bg-surface text-on-surface">🇬🇧 English (UK)</option>
            </select>
          </div>

          <span className="text-[11px] font-mono text-on-surface-variant bg-surface-container px-2 py-1 rounded border border-outline-variant/30">
            {wordCount} words
          </span>

          <button
            type="button"
            onClick={handleToggleEdit}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-mono transition-colors border ${
              isEditing
                ? 'bg-secondary/15 text-secondary border-secondary/40'
                : 'bg-surface-container hover:bg-surface-container-high text-on-surface-variant border-outline-variant/30'
            }`}
            title={isEditing ? 'Save edits to transcript' : 'Click to directly edit/adjust speech transcript'}
          >
            {isEditing ? <Check size={12} /> : <Edit3 size={12} />}
            <span>{isEditing ? 'Save Edit' : 'Edit Transcript'}</span>
          </button>

          {onToggleMic && (
            <button
              type="button"
              onClick={onToggleMic}
              className={`p-1.5 rounded-lg text-xs transition-colors border ${
                isListening
                  ? 'bg-surface-container hover:bg-surface-container-high text-on-surface-variant border-outline-variant/30'
                  : 'bg-secondary/15 text-secondary border-secondary/40'
              }`}
              title={isListening ? 'Pause Microphone' : 'Resume Microphone'}
            >
              {isListening ? <Mic size={14} /> : <MicOff size={14} />}
            </button>
          )}
        </div>
      </div>

      {/* Streaming Text Output or Direct Editable Textarea */}
      {isEditing ? (
        <div className="space-y-1">
          <textarea
            value={manualText}
            onChange={(e) => setManualText(e.target.value)}
            rows={3}
            placeholder="Edit or refine your technical answer text directly here..."
            className="w-full p-3 text-xs text-on-surface border border-primary/50 rounded-lg focus:outline-none focus:ring-1 focus:ring-primary bg-surface-container leading-relaxed font-mono"
          />
          <span className="text-[10px] text-outline font-mono italic block">
            Directly adjust any words before submitting. Real-time acoustic recovery remains active.
          </span>
        </div>
      ) : (
        <div className="relative min-h-[64px] max-h-40 overflow-y-auto p-3.5 bg-surface-container-lowest border border-outline-variant/20 rounded-lg text-sm text-on-surface leading-relaxed font-mono select-text">
          <span className="font-semibold text-on-surface">{finalizedText}</span>{' '}
          <span className="text-secondary/80 italic">{provisionalText}</span>
          {!finalizedText && !provisionalText && !typedFallback && (
            <span className="text-outline italic text-xs">
              {isListening
                ? 'Listening continuously... Speak your full technical answer clearly into the microphone. There is no word or time limit.'
                : 'Waiting for prompt...'}
            </span>
          )}
        </div>
      )}

      {/* Live Acoustic Recovery Chips (Proves 0.0 Marks Deducted in Real Time) */}
      {recovery.auditItems.length > 0 && (
        <div className="flex items-center gap-1.5 flex-wrap p-2 text-xs font-mono text-secondary bg-surface-container rounded-lg border border-secondary/30">
          <div className="flex items-center gap-1 font-bold">
            <ShieldCheck size={14} className="text-secondary" />
            <span>Acoustic Recovery Active:</span>
          </div>
          {recovery.auditItems.slice(0, 3).map((item, idx) => (
            <span key={idx} className="bg-surface-container-high px-2 py-0.5 rounded border border-outline-variant/30 text-[10px]">
              "{item.original}" → <strong className="text-secondary">{item.recovered}</strong>
            </span>
          ))}
          <span className="text-[10px] text-secondary font-mono italic ml-auto font-bold">
            0.0 Marks Deducted
          </span>
        </div>
      )}

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
            className="flex-1 px-3 py-2 text-xs border border-outline-variant/30 rounded-lg text-on-surface focus:outline-none focus:ring-1 focus:ring-primary bg-surface-container resize-y font-mono leading-relaxed"
          />

          <div className="flex flex-col gap-1.5">
            <button
              type="submit"
              disabled={isProcessing || wordCount === 0}
              className="flex items-center justify-center gap-1.5 px-4 py-2 bg-primary-container hover:bg-primary-fixed-dim text-on-primary-container font-mono font-bold rounded-lg text-xs shadow-[0_0_20px_rgba(108,136,255,0.4)] disabled:opacity-50 transition-all shrink-0"
            >
              <Send size={12} />
              <span>{isProcessing ? 'Evaluating...' : `Submit Answer (${wordCount} words)`}</span>
            </button>

            {wordCount > 0 && (
              <button
                type="button"
                onClick={handleClearAnswer}
                disabled={isProcessing}
                title="Clear and re-speak answer"
                className="flex items-center justify-center gap-1 px-2.5 py-1.5 bg-surface-container hover:bg-surface-container-high text-on-surface-variant rounded-lg text-xs font-mono border border-outline-variant/30 transition-colors"
              >
                <RotateCcw size={12} />
                <span>Clear</span>
              </button>
            )}
          </div>
        </div>

        {typedFallback.trim() && spokenText && (
          <div className="flex items-center gap-2 text-[11px] font-mono text-outline pt-0.5">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={overrideWithTyped}
                onChange={(e) => setOverrideWithTyped(e.target.checked)}
                className="rounded text-primary focus:ring-0 cursor-pointer"
              />
              <span>Replace microphone audio with typed text only</span>
            </label>
            <span className="text-outline-variant">•</span>
            <span className="italic">
              {overrideWithTyped ? 'Using typed text' : 'Combining speech + typed text'}
            </span>
          </div>
        )}
      </form>
    </div>
  );
};
