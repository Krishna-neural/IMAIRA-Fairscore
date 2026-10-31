import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';

interface RubricCoverageProps {
  flags: Record<string, 'covered' | 'partial' | 'missing'>;
}

export const RubricCoverage: React.FC<RubricCoverageProps> = ({ flags }) => {
  const entries = Object.entries(flags);

  return (
    <div className="bg-surface-container-low border border-outline-variant/30 rounded-xl p-5 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)] space-y-3">
      <div>
        <h3 className="text-sm font-bold text-on-surface">
          Semantic Rubric Proposition Coverage
        </h3>
        <p className="text-xs text-outline font-mono mt-0.5">
          Evaluated conceptually invariant to surface vocabulary, regional accents, or minor grammar variations:
        </p>
      </div>

      <div className="space-y-2">
        {entries.length > 0 ? (
          entries.map(([key, val]) => (
            <div
              key={key}
              className={`flex items-center justify-between p-3 rounded-lg border text-xs font-mono ${
                val === 'covered'
                  ? 'bg-secondary/10 border-secondary/30 text-secondary'
                  : val === 'partial'
                  ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                  : 'bg-error-container/20 border-error/30 text-error'
              }`}
            >
              <div className="flex items-center gap-2">
                {val === 'covered' ? (
                  <CheckCircle2 size={16} className="text-secondary" />
                ) : val === 'partial' ? (
                  <AlertTriangle size={16} className="text-amber-400" />
                ) : (
                  <XCircle size={16} className="text-error" />
                )}
                <span className="font-semibold text-on-surface">{key}</span>
              </div>
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                  val === 'covered'
                    ? 'bg-secondary/20 text-secondary border border-secondary/40'
                    : val === 'partial'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                    : 'bg-error-container/40 text-error border border-error/50'
                }`}
              >
                {val}
              </span>
            </div>
          ))
        ) : (
          <div className="text-xs font-mono text-outline italic p-3 bg-surface-container border border-outline-variant/20 rounded-lg">
            Satisfied core conceptual proposition benchmarks across active domain questions.
          </div>
        )}
      </div>
    </div>
  );
};
