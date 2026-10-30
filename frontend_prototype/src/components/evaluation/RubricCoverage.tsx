import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';

interface RubricCoverageProps {
  flags: Record<string, 'covered' | 'partial' | 'missing'>;
}

export const RubricCoverage: React.FC<RubricCoverageProps> = ({ flags }) => {
  const entries = Object.entries(flags);

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
      <h3 className="text-base font-bold text-[#101C35] mb-1">
        Semantic Rubric Proposition Coverage
      </h3>
      <p className="text-xs text-slate-500 mb-3.5">
        Evaluated conceptually invariant to surface vocabulary, regional accents, or minor grammar variations:
      </p>

      <div className="space-y-2">
        {entries.length > 0 ? (
          entries.map(([key, val]) => (
            <div
              key={key}
              className={`flex items-center justify-between p-2.5 rounded border text-xs ${
                val === 'covered'
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                  : val === 'partial'
                  ? 'bg-amber-50 border-amber-200 text-amber-900'
                  : 'bg-red-50 border-red-200 text-red-900'
              }`}
            >
              <div className="flex items-center gap-2">
                {val === 'covered' ? (
                  <CheckCircle2 size={16} className="text-emerald-700" />
                ) : val === 'partial' ? (
                  <AlertTriangle size={16} className="text-amber-700" />
                ) : (
                  <XCircle size={16} className="text-red-700" />
                )}
                <span className="font-semibold text-slate-800">{key}</span>
              </div>
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase ${
                  val === 'covered'
                    ? 'bg-emerald-200 text-emerald-900'
                    : val === 'partial'
                    ? 'bg-amber-200 text-amber-900'
                    : 'bg-red-200 text-red-900'
                }`}
              >
                {val}
              </span>
            </div>
          ))
        ) : (
          <div className="text-xs text-slate-500 italic p-3 bg-slate-50 border border-slate-200 rounded">
            Satisfied core conceptual proposition benchmarks across active domain questions.
          </div>
        )}
      </div>
    </div>
  );
};
