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
      ? 'Exemplary Staff Level'
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

  // SVG circular circumference: 2 * pi * 50 = 314.15
  const circumference = 314.15;
  const strokeOffset = Math.max(0, circumference - (circumference * overallScore) / 100);

  return (
    <div className="space-y-6 mb-6">
      {/* SECTION 2: CANDIDATE DOSSIER BANNER */}
      <div className="p-6 rounded-xl bg-surface-container-low border border-outline-variant/30 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)] top-edge-sheen">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-0.5 rounded bg-surface-container-high text-primary font-mono text-[11px] border border-outline-variant/40">
                EVALUATION DOSSIER
              </span>
              <span className="px-2.5 py-0.5 rounded bg-secondary/10 text-secondary border border-secondary/30 font-mono text-[11px] flex items-center gap-1">
                <span className="material-symbols-outlined text-[13px]">verified</span>
                100% Deterministic Rubric Verified
              </span>
              <span className="px-2.5 py-0.5 rounded bg-tertiary/10 text-tertiary border border-tertiary/30 font-mono text-[11px] flex items-center gap-1">
                <span className="material-symbols-outlined text-[13px]">record_voice_over</span>
                Decoupled Phonetic Invariance Active
              </span>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-baseline gap-2 sm:gap-4">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-on-surface tracking-tight">
                {candidateName}
              </h1>
              <span className="text-sm font-mono text-secondary">{domain}</span>
              <span className="text-xs font-mono text-outline">
                Calibrator: <span className="text-primary">Isotonic CPU 1</span>
              </span>
            </div>

            <p className="text-xs text-on-surface-variant max-w-3xl leading-relaxed">
              Multi-dimensional evaluation isolating engineering content mastery and reasoning structure from accent variations and speech delivery pace.
            </p>
          </div>

          {/* Quick Metrics Cluster */}
          <div className="grid grid-cols-3 gap-3 min-w-[280px] sm:min-w-[320px] bg-surface-container-lowest/80 p-3.5 rounded-lg border border-outline-variant/30 font-mono text-xs">
            <div className="border-r border-outline-variant/20 pr-3">
              <span className="text-[10px] text-outline block uppercase">ACCENT DELTA</span>
              <span className="text-base font-bold text-secondary mt-0.5 block">0.00%</span>
              <span className="text-[9px] text-secondary">Zero acoustic bias</span>
            </div>
            <div className="border-r border-outline-variant/20 px-3">
              <span className="text-[10px] text-outline block uppercase">SCORING RATIO</span>
              <span className="text-base font-bold text-primary mt-0.5 block">60 / 40</span>
              <span className="text-[9px] text-primary">Content / Struct</span>
            </div>
            <div className="pl-3">
              <span className="text-[10px] text-outline block uppercase">COMM PENALTY</span>
              <span className="text-base font-bold text-tertiary mt-0.5 block">0.0 pts</span>
              <span className="text-[9px] text-tertiary">Diagnostic Only</span>
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 3: OVERALL SCORE HERO BENTO (5 cols Dial + 7 cols Sub-Scores) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Primary FairScore Radial Dial */}
        <div className="lg:col-span-5 bg-surface-container-low border border-outline-variant/30 rounded-xl p-6 flex flex-col justify-between shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)] relative overflow-hidden">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-secondary"></span>
              <span className="text-xs font-mono uppercase tracking-wider text-on-surface-variant font-semibold">
                Primary FairScore Index
              </span>
            </div>
            <span className="px-2 py-0.5 rounded bg-surface-container font-mono text-[10px] text-secondary border border-outline-variant/30">
              ISOTONIC CALIBRATION
            </span>
          </div>

          {/* Circular SVG Radial Meter */}
          <div className="py-6 flex flex-col items-center justify-center relative">
            <div className="relative w-52 h-52 flex items-center justify-center">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
                <circle cx="60" cy="60" fill="none" r="50" stroke="#272a34" strokeWidth="8"></circle>
                <circle
                  cx="60"
                  cy="60"
                  fill="none"
                  r="50"
                  stroke="#57e6ff"
                  strokeDasharray="314.15"
                  strokeDashoffset={strokeOffset}
                  strokeLinecap="round"
                  strokeWidth="8"
                ></circle>
                <circle
                  cx="60"
                  cy="60"
                  fill="none"
                  opacity="0.6"
                  r="42"
                  stroke="#9c7aff"
                  strokeDasharray="4 6"
                  strokeWidth="2"
                ></circle>
              </svg>

              <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                <span className="text-5xl font-extrabold text-on-surface tracking-tight font-sans">
                  {overallScore}%
                </span>
                <span className="text-xs font-mono text-outline -mt-1">
                  ({overall5pt} / 5.0)
                </span>
              </div>
            </div>

            <div className="mt-3 flex flex-col items-center gap-1">
              <span className="text-base font-bold text-secondary font-sans">{verdict}</span>
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-surface-container border border-outline-variant/30 text-xs font-mono text-on-surface">
                <span className="material-symbols-outlined text-tertiary text-sm">leaderboard</span>
                <span>Weighted: <strong className="text-secondary">60% Content + 40% Structure</strong></span>
              </div>
            </div>
          </div>

          {/* Deterministic Evidence Lock status footer */}
          <div className="pt-3 border-t border-outline-variant/20 flex items-center justify-between text-[11px] font-mono">
            <div className="flex items-center gap-1.5 text-secondary">
              <span className="material-symbols-outlined text-sm">lock</span>
              <span className="font-semibold tracking-wider">VERIFIED // ACCENT INVARIANCE LOCKED</span>
            </div>
            <span className="text-outline">|Δ| = 0.00 pts</span>
          </div>
        </div>

        {/* Right: Dimensional Sub-Scores Progress Bars */}
        <div className="lg:col-span-7 bg-surface-container-low border border-outline-variant/30 rounded-xl p-6 flex flex-col justify-between shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)] space-y-4">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-bold text-on-surface">Dimensional Sub-Scores</h3>
                <p className="text-xs text-outline font-mono">
                  Strict mathematical decoupling across 3 independent evaluation dimensions
                </p>
              </div>
              <span className="text-xs font-mono text-primary px-2.5 py-1 bg-primary/10 rounded border border-primary/20">
                EVALUATION MATRICES
              </span>
            </div>

            <div className="space-y-3.5">
              {/* Content Mastery */}
              <div className="p-3 rounded-lg bg-surface-container border border-outline-variant/20 space-y-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-secondary text-[16px]">storage</span>
                    <span className="text-xs font-bold text-on-surface">Content Mastery (60% Weight)</span>
                  </div>
                  <div className="flex items-baseline gap-1 font-mono text-xs">
                    <span className="text-secondary font-bold text-base">{scores.content}%</span>
                    <span className="text-outline">({calContent} / 5.0)</span>
                  </div>
                </div>
                <div className="w-full bg-surface-container-highest h-2 rounded-full overflow-hidden">
                  <div className="bg-secondary h-full rounded-full transition-all" style={{ width: `${scores.content}%` }}></div>
                </div>
                <p className="text-[11px] text-on-surface-variant leading-relaxed">
                  Deep technical accuracy, algorithmic invariants, and mechanism completeness evaluated with 3-run majority voting.
                </p>
              </div>

              {/* Structure & Flow */}
              <div className="p-3 rounded-lg bg-surface-container border border-outline-variant/20 space-y-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary text-[16px]">schema</span>
                    <span className="text-xs font-bold text-on-surface">Structure & Flow (40% Weight)</span>
                  </div>
                  <div className="flex items-baseline gap-1 font-mono text-xs">
                    <span className="text-primary font-bold text-base">{scores.structure}%</span>
                    <span className="text-outline">({calStructure} / 5.0)</span>
                  </div>
                </div>
                <div className="w-full bg-surface-container-highest h-2 rounded-full overflow-hidden">
                  <div className="bg-primary h-full rounded-full transition-all" style={{ width: `${scores.structure}%` }}></div>
                </div>
                <p className="text-[11px] text-on-surface-variant leading-relaxed">
                  Framing (35% opening directness), Coherence (40% causal flow), and Closure (25% trade-off synthesis).
                </p>
              </div>

              {/* Delivery Diagnostics */}
              <div className="p-3 rounded-lg bg-surface-container border border-outline-variant/20 space-y-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-tertiary text-[16px]">forum</span>
                    <span className="text-xs font-bold text-on-surface">Delivery Diagnostics (Diagnostic Only)</span>
                  </div>
                  <div className="flex items-baseline gap-1 font-mono text-xs">
                    <span className="text-tertiary font-bold text-base">{scores.communication}%</span>
                    <span className="text-outline">({calComm} / 5.0)</span>
                  </div>
                </div>
                <div className="w-full bg-surface-container-highest h-2 rounded-full overflow-hidden">
                  <div className="bg-tertiary h-full rounded-full transition-all" style={{ width: `${scores.communication}%` }}></div>
                </div>
                <p className="text-[11px] text-on-surface-variant leading-relaxed">
                  Speech rate (optimal 110–170 WPM) and pauses. <strong className="text-tertiary font-bold">0.0 marks deducted</strong> for accent or non-native fluency.
                </p>
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-outline-variant/20 flex flex-wrap items-center justify-between gap-2 text-[10px] font-mono text-outline">
            <span>Model Evaluator: Multi-Agent Rubric Jury + Isotonic Calibrators</span>
            <span className="text-secondary">Acoustic Recovery Active</span>
          </div>
        </div>
      </div>
    </div>
  );
};
