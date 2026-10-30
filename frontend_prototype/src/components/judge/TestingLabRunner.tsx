import React, { useState, useEffect } from 'react';
import { Play, CheckCircle2, XCircle, RotateCcw } from 'lucide-react';
import { apiService } from '../../services/apiService';

export const TestingLabRunner: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [stats, setStats] = useState({ passed: 0, failed: 0 });

  const runTests = async () => {
    setLoading(true);
    try {
      const data = await apiService.runAllTests();
      setResults(data.results || []);
      setStats({ passed: data.passed || 0, failed: data.failed || 0 });
    } catch (err: any) {
      console.error('[TestingLab] Error running tests:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runTests();
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-5 bg-surface-container-low border border-outline-variant/30 rounded-xl shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)]">
        <div>
          <h3 className="text-sm font-bold text-on-surface">
            Automated Testing Lab (18 Verification Categories)
          </h3>
          <p className="text-xs text-outline font-mono mt-0.5">
            Executes real unit and integration test assertions directly against the active FastAPI backend:
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="px-3 py-1 rounded-lg bg-secondary/15 text-secondary font-bold border border-secondary/30">
            {stats.passed} PASSED
          </span>
          {stats.failed > 0 && (
            <span className="px-3 py-1 rounded-lg bg-error-container/40 text-error font-bold border border-error/50">
              {stats.failed} FAILED
            </span>
          )}
          <button
            onClick={runTests}
            disabled={loading}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-primary-container hover:bg-primary-fixed-dim text-on-primary-container rounded-lg text-xs font-bold shadow-sm disabled:opacity-50 transition-all"
          >
            <RotateCcw size={12} className={loading ? 'animate-spin' : ''} />
            <span>{loading ? 'Executing Suite...' : 'Re-run Tests'}</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {results.map((t, idx) => (
          <div
            key={idx}
            className={`p-4 bg-surface-container-low border rounded-xl shadow-sm flex flex-col justify-between font-mono text-xs transition-colors ${
              t.passed ? 'border-l-4 border-l-secondary border-outline-variant/25' : 'border-l-4 border-l-error border-outline-variant/25'
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span
                  className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[10px] font-bold border ${
                    t.passed ? 'bg-secondary/15 text-secondary border-secondary/30' : 'bg-error-container/40 text-error border-error/50'
                  }`}
                >
                  {t.passed ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
                  {t.passed ? 'PASSED' : 'FAILED'} ({t.latency_ms}ms)
                </span>
                <span className="text-[11px] text-outline">{t.category}</span>
              </div>

              <h4 className="text-xs font-bold text-on-surface mb-1 font-sans">{t.test_name}</h4>

              <div className="text-[11px] text-on-surface-variant space-y-1 pt-1">
                <div className="text-outline">
                  <strong>Input: </strong>"{t.input_description}"
                </div>
                <div className="text-secondary">
                  <strong>Expected: </strong>{t.expected_behavior}
                </div>
                <div className="text-on-surface">
                  <strong>Observed: </strong>{t.observed_result}
                </div>
              </div>
            </div>

            <div className="mt-3 pt-2 border-t border-outline-variant/20 flex items-center justify-between text-[10px] text-outline">
              <span>Assertion: {t.assertion}</span>
              <span className="text-primary">{t.test_id}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
