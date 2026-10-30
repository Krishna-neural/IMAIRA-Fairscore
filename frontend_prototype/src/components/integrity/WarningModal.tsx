import React from 'react';
import { AlertTriangle, AlertCircle, ShieldAlert, X } from 'lucide-react';
import { IntegrityWarning } from '../../types/integrity';

interface WarningModalProps {
  warning: IntegrityWarning | null;
  onDismiss: () => void;
}

export const WarningModal: React.FC<WarningModalProps> = ({ warning, onDismiss }) => {
  if (!warning) return null;

  const isFinal = warning.warningNumber === 3;
  const isSecond = warning.warningNumber === 2;

  const badgeColor = isFinal
    ? 'bg-error-container/40 text-error border-error/50'
    : isSecond
    ? 'bg-orange-500/20 text-orange-300 border-orange-500/40'
    : 'bg-amber-500/20 text-amber-300 border-amber-500/40';

  const dateStr = new Date(warning.timestamp).toLocaleTimeString();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-surface-container-lowest/80 backdrop-blur-md animate-fadeIn">
      <div className="w-full max-w-lg bg-surface-container-low rounded-2xl shadow-[0_24px_60px_rgba(0,0,0,0.85)] border border-outline-variant/30 overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-outline-variant/20 flex items-center justify-between bg-surface-container">
          <div className="flex items-center gap-2">
            {isFinal ? (
              <ShieldAlert className="text-error" size={22} />
            ) : (
              <AlertTriangle className={isSecond ? 'text-orange-400' : 'text-amber-400'} size={22} />
            )}
            <h3 className="text-sm font-mono font-bold text-on-surface">
              {isFinal
                ? 'CRITICAL INTEGRITY WARNING 3/3'
                : `INTEGRITY WARNING ${warning.warningNumber}/3`}
            </h3>
          </div>
          <button
            onClick={onDismiss}
            className="p-1 text-outline hover:text-on-surface rounded"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 space-y-3.5 text-xs font-mono text-on-surface-variant">
          <div className="flex items-center justify-between">
            <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${badgeColor}`}>
              Warning {warning.warningNumber} of 3
            </span>
            <span className="text-[10px] text-outline font-mono">Timestamp: {dateStr}</span>
          </div>

          <div className="bg-surface-container border border-outline-variant/30 rounded-lg p-3 text-xs space-y-1">
            <div className="font-semibold text-on-surface uppercase tracking-wide">
              Observed Event:
            </div>
            <p className="text-secondary font-medium">{warning.event.description}</p>
            <p className="text-outline">{warning.event.details}</p>
          </div>

          <div className="space-y-1">
            <div className="font-semibold text-on-surface text-[11px] uppercase tracking-wide">
              Detailed Explanation:
            </div>
            <p className="leading-relaxed text-on-surface-variant">{warning.explanation}</p>
          </div>

          <div className="bg-primary/10 border border-primary/20 rounded-lg p-3 text-xs text-primary space-y-1">
            <div className="font-semibold uppercase tracking-wide text-primary">
              Required Corrective Action:
            </div>
            <p>{warning.correctiveAction}</p>
          </div>

          {isFinal && (
            <div className="p-2.5 bg-error-container/30 border border-error/40 rounded-lg text-xs text-error font-medium">
              ⚠️ Attention: Any further verified violation will immediately terminate the session and initiate a 24-hour interviewer restriction.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3.5 bg-surface-container border-t border-outline-variant/20 flex justify-end gap-2">
          <button
            onClick={onDismiss}
            className="px-4 py-2 rounded-lg font-mono font-bold text-xs text-on-primary-container bg-primary-container hover:bg-primary-fixed-dim transition-colors shadow-sm"
          >
            I Acknowledge & Comply
          </button>
        </div>
      </div>
    </div>
  );
};
