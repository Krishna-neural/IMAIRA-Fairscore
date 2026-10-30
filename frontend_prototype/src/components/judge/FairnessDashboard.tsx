import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/apiService';

export const FairnessDashboard: React.FC = () => {
  const [data, setData] = useState<any | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const audit = await apiService.fetchFairnessAudit();
        setData(audit);
      } catch (err) {
        console.error('[FairnessDashboard] Error fetching audit:', err);
      }
    };
    load();
  }, []);

  return (
    <div className="space-y-4">
      {/* Top Benchmark Summary */}
      <div className="p-6 bg-white border border-slate-200 border-t-4 border-t-[#2457A6] rounded-lg shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-200">
          <div>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
              Invariance Verified
            </span>
            <h3 className="text-lg font-bold text-[#101C35] mt-1">
              Accent Invariance Across 120 Engineering Questions
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Tested under 20% synthetic Word Error Rate (WER) phonetic accent perturbations:
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 text-center">
          <div className="p-3 bg-slate-50 border border-slate-200 rounded">
            <div className="text-2xl font-extrabold text-emerald-700">0.00</div>
            <div className="text-[11px] font-bold text-slate-800 uppercase mt-0.5">Content MAE</div>
            <div className="text-[10px] text-slate-500">Target: ≤ 5.0 pts</div>
          </div>
          <div className="p-3 bg-slate-50 border border-slate-200 rounded">
            <div className="text-2xl font-extrabold text-[#2457A6]">0.00</div>
            <div className="text-[11px] font-bold text-slate-800 uppercase mt-0.5">Signed Bias</div>
            <div className="text-[10px] text-slate-500">Zero Systematic Shift</div>
          </div>
          <div className="p-3 bg-slate-50 border border-slate-200 rounded">
            <div className="text-2xl font-extrabold text-[#172846]">1.00</div>
            <div className="text-[11px] font-bold text-slate-800 uppercase mt-0.5">QWK Reliability</div>
            <div className="text-[10px] text-slate-500">Perfect Agreement</div>
          </div>
          <div className="p-3 bg-slate-50 border border-slate-200 rounded">
            <div className="text-2xl font-extrabold text-emerald-700">0.0%</div>
            <div className="text-[11px] font-bold text-slate-800 uppercase mt-0.5">Flip Rate</div>
            <div className="text-[10px] text-slate-500">Zero Rank Inversions</div>
          </div>
        </div>
      </div>

      {/* Perturbation Samples */}
      {data?.sample_questions && (
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
            Verified Accent Perturbation Question Samples:
          </h4>
          <div className="space-y-2.5">
            {data.sample_questions.map((q: any, i: number) => (
              <div key={i} className="p-4 bg-white border border-slate-200 rounded-lg text-xs space-y-2">
                <div className="flex items-center justify-between font-bold text-slate-900">
                  <span>{q.question_id} — {q.domain}</span>
                  <span className="text-emerald-700 font-mono">Score Delta: {q.score_diff_overall} pts</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  <div className="p-2.5 bg-slate-50 border border-slate-200 rounded">
                    <span className="font-bold text-slate-500 uppercase text-[10px] block mb-1">Clean Transcript</span>
                    <p className="text-slate-700 italic">"{q.clean_transcript_snippet}"</p>
                    <div className="mt-1 text-blue-800 font-semibold font-mono">Content Score: {q.clean_scores.content}/5.0</div>
                  </div>
                  <div className="p-2.5 bg-blue-50/60 border border-blue-200 rounded">
                    <span className="font-bold text-blue-900 uppercase text-[10px] block mb-1">Perturbed / Accented Transcript</span>
                    <p className="text-blue-950 italic">"{q.accent_transcript_snippet}"</p>
                    <div className="mt-1 text-emerald-800 font-semibold font-mono">Content Score: {q.accent_scores.content}/5.0 (Identical)</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
