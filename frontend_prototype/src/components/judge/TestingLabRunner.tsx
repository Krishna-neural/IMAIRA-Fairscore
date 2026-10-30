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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 bg-white border border-slate-200 rounded-lg">
        <div>
          <h3 className="text-base font-bold text-[#101C35]">
            Automated Testing Lab (18 Categories)
          </h3>
          <p className="text-xs text-slate-500">
            Executes real unit and integration test assertions directly against the active FastAPI backend:
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded bg-emerald-100 text-emerald-800 text-xs font-bold border border-emerald-300">
            {stats.passed} PASSED
          </span>
          <span className="px-2.5 py-1 rounded bg-red-100 text-red-800 text-xs font-bold border border-red-300">
            {stats.failed} FAILED
          </span>
          <button
            onClick={runTests}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#2457A6] hover:bg-[#1A4482] text-white rounded text-xs font-semibold shadow-xs disabled:opacity-50 transition-colors"
          >
            <RotateCcw size={12} className={loading ? 'animate-spin' : ''} />
            <span>{loading ? 'Running 18 Tests...' : 'Re-run Tests'}</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {results.map((t, idx) => (
          <div
            key={idx}
            className={`p-3.5 bg-white border rounded-lg shadow-xs flex flex-col justify-between ${
              t.passed ? 'border-l-4 border-l-emerald-600 border-slate-200' : 'border-l-4 border-l-red-600 border-slate-200'
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold ${
                    t.passed ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                  }`}
                >
                  {t.passed ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
                  {t.passed ? 'PASSED' : 'FAILED'} ({t.latency_ms}ms)
                </span>
                <span className="text-[11px] font-semibold text-slate-500">{t.category}</span>
              </div>

              <h4 className="text-xs font-bold text-[#101C35] mb-1">{t.test_name}</h4>

              <div className="text-[11px] text-slate-600 space-y-0.5">
                <div><span className="font-semibold text-slate-700">Input:</span> {t.input}</div>
                <div><span className="font-semibold text-blue-700">Expected:</span> {t.expected}</div>
                <div><span className="font-semibold text-emerald-700">Actual:</span> {t.actual}</div>
              </div>
            </div>

            <div className="mt-2 p-1.5 bg-slate-50 border border-slate-200 rounded text-[10px] font-mono text-slate-800 truncate">
              {t.evidence}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
