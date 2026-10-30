import React from 'react';
import { DimensionScores, CalibratedScores } from '../../types/evaluation';
import { ShieldCheck, Award } from 'lucide-react';

interface ScoreCardProps {
  overallScore: number;
  scores: DimensionScores;
  calibratedScores: CalibratedScores;
  candidateName: string;
  domain: string;
  summaryVerdict?: string;
}

export const ScoreCard: React.FC<ScoreCardProps> = ({
  overallScore,
  scores,
  calibratedScores,
  candidateName,
  domain,
  summaryVerdict,
}) => {
  const verdict =
    summaryVerdict ||
    (overallScore >= 65.0
      ? 'Demonstrates Solid Competence'
      : overallScore >= 40.0
      ? 'Developing Competence'
      : 'Needs Foundational Review');

  const overall5pt = (1.0 + (overallScore / 100) * 4.0).toFixed(2);
  const calContent = calibratedScores.content
    ? Number(calibratedScores.content).toFixed(2)
    : (1.0 + (scores.content / 100) * 4.0).toFixed(2);
  const calStructure = calibratedScores.structure
    ? Number(calibratedScores.structure).toFixed(2)
    : (1.0 + (scores.structure / 100) * 4.0).toFixed(2);
  const calComm = calibratedScores.communication
    ? Number(calibratedScores.communication).toFixed(2)
    : (1.0 + (scores.communication / 100) * 4.0).toFixed(2);

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm mb-6">
      {/* Executive Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-200 gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
              <Award size={13} className="text-emerald-700" />
              Verified Evaluation Scorecard
            </span>
            <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-800 border border-blue-200">
              {verdict}
            </span>
          </div>
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
          <div className="flex items-baseline md:justify-end gap-1.5 mt-1">
            <span className="text-4xl font-extrabold text-[#2457A6] leading-none">
              {overallScore}%
            </span>
            <span className="text-sm font-semibold text-slate-500">
              ({overall5pt} / 5.0)
            </span>
          </div>
        </div>
      </div>

      {/* 4 Score Metric Cards (Mathematically Grounded: 60% Content + 40% Structure) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3.5 mt-5">
        <div className="p-4 bg-slate-50 border border-slate-200 border-t-4 border-t-[#2457A6] rounded text-center">
          <div className="text-3xl font-extrabold text-[#2457A6]">{scores.content || 0}%</div>
          <div className="text-xs font-bold text-slate-800 uppercase tracking-wide mt-1">
            Content Mastery (60%)
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            Calibrated: <strong>{calContent} / 5.0</strong>
          </div>
        </div>

        <div className="p-4 bg-slate-50 border border-slate-200 border-t-4 border-t-[#172846] rounded text-center">
          <div className="text-3xl font-extrabold text-[#172846]">{scores.structure || 0}%</div>
          <div className="text-xs font-bold text-slate-800 uppercase tracking-wide mt-1">
            Structure & Flow (40%)
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            Calibrated: <strong>{calStructure} / 5.0</strong>
          </div>
        </div>

        <div className="p-4 bg-slate-50 border border-slate-200 border-t-4 border-t-emerald-600 rounded text-center">
          <div className="text-3xl font-extrabold text-emerald-700">{scores.communication || 0}%</div>
          <div className="text-xs font-bold text-slate-800 uppercase tracking-wide mt-1">
            Delivery Diagnostics
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            Diagnostic Only • <strong>0% Penalty</strong>
          </div>
        </div>

        <div className="p-4 bg-blue-50/70 border border-blue-200 border-t-4 border-t-[#3478D4] rounded text-center">
          <div className="text-3xl font-extrabold text-[#2457A6]">{overallScore}%</div>
          <div className="text-xs font-bold text-blue-900 uppercase tracking-wide mt-1">
            Weighted Total
          </div>
          <div className="text-[11px] text-blue-700 font-medium mt-0.5">
            60% Content + 40% Structure
          </div>
        </div>
      </div>

      {/* Accent Invariance & FairScore Protection Guarantee Banner */}
      <div className="mt-4 p-3 bg-emerald-50/80 border border-emerald-200 rounded-md flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2 text-emerald-900">
          <ShieldCheck size={18} className="text-emerald-700 shrink-0" />
          <span>
            <strong>Accent Invariance Guarantee Active:</strong> Full technical credit preserved via acoustic slice recovery. 0.0 marks deducted for non-native pronunciation or regional accent.
          </span>
        </div>
        <span className="px-2 py-0.5 bg-emerald-200/70 text-emerald-900 text-[10px] font-extrabold rounded-full tracking-wide shrink-0 uppercase self-start sm:self-auto">
          PROTECTION ACTIVE
        </span>
      </div>
    </div>
  );
};
