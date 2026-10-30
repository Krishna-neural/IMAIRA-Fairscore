import React from 'react';
import { DimensionScores, CalibratedScores } from '../../types/evaluation';

interface ScoreCardProps {
  overallScore: number;
  scores: DimensionScores;
  calibratedScores: CalibratedScores;
  candidateName: string;
  domain: string;
}

export const ScoreCard: React.FC<ScoreCardProps> = ({
  overallScore,
  scores,
  calibratedScores,
  candidateName,
  domain,
}) => {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm mb-6">
      {/* Executive Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-200 gap-4">
        <div>
          <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 mb-1.5">
            Verified Evaluation Scorecard
          </span>
          <h2 className="text-2xl font-extrabold text-[#101C35]">
            Technical Competence Assessment
          </h2>
          <div className="text-xs text-slate-500 mt-1">
            Candidate: <strong className="text-slate-800">{candidateName}</strong> • Domain: <strong className="text-slate-800">{domain}</strong> • Calibration: <strong className="text-slate-800">Isotonic Regression (CPU 1)</strong>
          </div>
        </div>

        <div className="text-left md:text-right">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
            Overall FairScore
          </span>
          <div className="text-4xl font-extrabold text-[#2457A6] leading-none mt-1">
            {overallScore}%
          </div>
        </div>
      </div>

      {/* 4 Score Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3.5 mt-5">
        <div className="p-4 bg-slate-50 border border-slate-200 border-t-4 border-t-[#2457A6] rounded text-center">
          <div className="text-3xl font-extrabold text-[#2457A6]">{scores.content || 0}%</div>
          <div className="text-xs font-bold text-slate-800 uppercase tracking-wide mt-1">
            Content Mastery (50%)
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            Calibrated: <strong>{calibratedScores.content || 0.0}/5.0</strong>
          </div>
        </div>

        <div className="p-4 bg-slate-50 border border-slate-200 border-t-4 border-t-[#172846] rounded text-center">
          <div className="text-3xl font-extrabold text-[#172846]">{scores.structure || 0}%</div>
          <div className="text-xs font-bold text-slate-800 uppercase tracking-wide mt-1">
            Structure & Flow (30%)
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            Calibrated: <strong>{calibratedScores.structure || 0.0}/5.0</strong>
          </div>
        </div>

        <div className="p-4 bg-slate-50 border border-slate-200 border-t-4 border-t-emerald-600 rounded text-center">
          <div className="text-3xl font-extrabold text-emerald-700">{scores.communication || 0}%</div>
          <div className="text-xs font-bold text-slate-800 uppercase tracking-wide mt-1">
            Communication (20%)
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            Calibrated: <strong>{calibratedScores.communication || 0.0}/5.0</strong>
          </div>
        </div>

        <div className="p-4 bg-blue-50/70 border border-blue-200 border-t-4 border-t-[#3478D4] rounded text-center">
          <div className="text-3xl font-extrabold text-[#2457A6]">{overallScore}%</div>
          <div className="text-xs font-bold text-blue-900 uppercase tracking-wide mt-1">
            Weighted Total
          </div>
          <div className="text-[11px] text-blue-700 font-medium mt-0.5">
            50% C • 30% S • 20% Comm
          </div>
        </div>
      </div>
    </div>
  );
};
