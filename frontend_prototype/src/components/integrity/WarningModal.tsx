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
    ? 'bg-red-100 text-red-800 border-red-300'
    : isSecond
    ? 'bg-orange-100 text-orange-800 border-orange-300'
    : 'bg-amber-100 text-amber-800 border-amber-300';

  const headerColor = isFinal
    ? 'bg-red-50 border-red-200 text-red-900'
    : isSecond
    ? 'bg-orange-50 border-orange-200 text-orange-900'
    : 'bg-amber-50 border-amber-200 text-amber-900';

  const dateStr = new Date(warning.timestamp).toLocaleTimeString();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-lg bg-white rounded-lg shadow-xl border border-slate-300 overflow-hidden">
        {/* Header */}
        <div className={`p-4 border-b flex items-center justify-between ${headerColor}`}>
          <div className="flex items-center gap-2">
            {isFinal ? (
              <ShieldAlert className="text-red-700" size={22} />
            ) : (
              <AlertTriangle className={isSecond ? 'text-orange-700' : 'text-amber-700'} size={22} />
            )}
            <h3 className="text-base font-bold">
              {isFinal
                ? 'FINAL WARNING 3/3 — Session Integrity Critical'
                : `INTEGRITY WARNING ${warning.warningNumber}/3`}
            </h3>
          </div>
          <button
            onClick={onDismiss}
            className="p-1 text-slate-500 hover:text-slate-700 rounded"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 space-y-3.5 text-sm text-slate-700">
          <div className="flex items-center justify-between">
            <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-bold border ${badgeColor}`}>
              Warning {warning.warningNumber} of 3
            </span>
            <span className="text-xs text-slate-500 font-mono">Timestamp: {dateStr}</span>
          </div>

          <div className="bg-slate-50 border border-slate-200 rounded p-3 text-xs space-y-1">
            <div className="font-semibold text-slate-900 uppercase tracking-wide">
              Observed Event:
            </div>
            <p className="text-slate-800 font-medium">{warning.event.description}</p>
            <p className="text-slate-500">{warning.event.details}</p>
          </div>

          <div className="space-y-1">
            <div className="font-semibold text-slate-900 text-xs uppercase tracking-wide">
              Detailed Explanation:
            </div>
            <p className="leading-relaxed">{warning.explanation}</p>
          </div>

          <div className="bg-blue-50/70 border border-blue-200 rounded p-3 text-xs text-blue-900 space-y-1">
            <div className="font-semibold uppercase tracking-wide text-blue-950">
              Required Corrective Action:
            </div>
            <p>{warning.correctiveAction}</p>
          </div>

          {isFinal && (
            <div className="p-2.5 bg-red-50 border border-red-200 rounded text-xs text-red-800 font-medium">
              ⚠️ Attention: Any further verified violation will immediately terminate the session and initiate a 24-hour interviewer restriction.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3.5 bg-slate-50 border-t border-slate-200 flex justify-end gap-2">
          <button
            onClick={onDismiss}
            className={`px-4 py-2 rounded font-semibold text-xs text-white transition-colors ${
              isFinal ? 'bg-red-700 hover:bg-red-800' : 'bg-blue-700 hover:bg-blue-800'
            }`}
          >
            I Acknowledge & Comply
          </button>
        </div>
      </div>
    </div>
  );
};
