import React, { useState } from 'react';
import { HumanAvatar } from '../components/avatar/HumanAvatar';
import { speechService } from '../services/speechService';
import { Volume2 } from 'lucide-react';

interface LandingPageProps {
  onStartInterview: () => void;
  onExploreJudge: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onStartInterview,
  onExploreJudge,
}) => {
  const [isPlayingDemo, setIsPlayingDemo] = useState(false);
  const [activePerspective, setActivePerspective] = useState<'student' | 'officer'>('student');

  const demoText =
    "Explain how Raft prevents split-brain scenarios during network partitions, and how randomized election timeouts guarantee term monotonicity.";

  const handleToggleDemo = () => {
    if (isPlayingDemo) {
      speechService.setMuted(true);
      setIsPlayingDemo(false);
      setTimeout(() => speechService.setMuted(false), 200);
    } else {
      setIsPlayingDemo(true);
      speechService.speak(demoText, () => {
        setIsPlayingDemo(false);
      });
    }
  };

  return (
    <div className="relative pt-6 pb-16 overflow-hidden space-y-16">
      {/* Atmospheric Aura Background */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[650px] glow-aura pointer-events-none -z-10"></div>
      <div className="absolute top-96 left-1/4 w-96 h-96 bg-secondary/5 rounded-full blur-[140px] pointer-events-none -z-10"></div>
      <div className="absolute top-72 right-1/4 w-96 h-96 bg-tertiary-container/10 rounded-full blur-[120px] pointer-events-none -z-10"></div>

      {/* HERO SECTION */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 pt-4 pb-12 text-center lg:pt-8">
        {/* Kernel Status Pill */}
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-surface-container-low border border-outline-variant/30 text-xs font-mono text-on-surface-variant mb-6 shadow-sm">
          <span className="w-2 h-2 rounded-full bg-secondary animate-pulse"></span>
          <span className="text-on-surface font-medium">IMAIRA KERNEL v4.2</span>
          <span className="text-outline">/</span>
          <span className="text-secondary font-medium">DECOUPLED FAIRNESS ENGINE</span>
          <span className="text-outline">/</span>
          <span className="text-tertiary">DETERMINISTIC LATENCY &lt; 320ms</span>
        </div>

        {/* Headline */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-on-surface max-w-5xl mx-auto tracking-tight mb-6 leading-tight">
          Get judged on your intelligence. <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-secondary via-primary to-tertiary bg-clip-text text-transparent">
            Not your accent.
          </span>
        </h1>

        {/* Supporting Subtitle */}
        <p className="text-base sm:text-lg text-on-surface-variant max-w-3xl mx-auto mb-8 leading-relaxed">
          An AI-powered technical interview platform that understands what you know, verifies what you say, and evaluates your engineering decisions with deterministic, evidence-based rubrics.
        </p>

        {/* Primary CTAs */}
        <div className="flex flex-wrap items-center justify-center gap-4 mb-10">
          <button
            onClick={onStartInterview}
            className="px-6 py-3 rounded-lg bg-primary-container text-on-primary-container text-sm font-semibold shadow-[0_0_30px_rgba(108,136,255,0.45)] hover:bg-primary-fixed-dim transition-all active:scale-[0.98] flex items-center space-x-2 border border-primary-fixed/20"
          >
            <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>
              rocket_launch
            </span>
            <span>Start AI Interview</span>
            <span className="bg-on-primary-container/20 text-on-primary-container text-[10px] font-mono px-2 py-0.5 rounded ml-1">
              ⌘K
            </span>
          </button>
          <button
            onClick={onExploreJudge}
            className="px-6 py-3 rounded-lg bg-surface-container-low border border-outline-variant/30 text-on-surface text-sm font-semibold hover:bg-surface-container-high hover:border-outline-variant/60 transition-all flex items-center space-x-2"
          >
            <span className="material-symbols-outlined text-secondary" style={{ fontSize: '20px' }}>
              architecture
            </span>
            <span>Explore Architecture</span>
          </button>
        </div>

        {/* Micro Metric Indicators */}
        <div className="flex flex-wrap items-center justify-center gap-4 text-xs font-mono text-on-surface-variant">
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-md bg-surface-container-low border border-outline-variant/20">
            <span className="material-symbols-outlined text-secondary" style={{ fontSize: '16px' }}>
              check_circle
            </span>
            <span>0.00% Accent Bias Variance (|Δ| = 0.00)</span>
          </div>
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-md bg-surface-container-low border border-outline-variant/20">
            <span className="material-symbols-outlined text-primary" style={{ fontSize: '16px' }}>
              speed
            </span>
            <span>Sub-320ms ASR Latency</span>
          </div>
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-md bg-surface-container-low border border-outline-variant/20">
            <span className="material-symbols-outlined text-tertiary" style={{ fontSize: '16px' }}>
              verified_user
            </span>
            <span>2,000-Term Glossary Recovery</span>
          </div>
        </div>
      </section>

      {/* INTERACTIVE PRODUCT SIMULATION FRAME */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="relative rounded-2xl bg-surface-container-low border border-outline-variant/30 shadow-[0_24px_60px_rgba(0,0,0,0.85)] overflow-hidden">
          {/* Window Chrome / Control Bar */}
          <div className="flex items-center justify-between px-4 py-3 bg-surface-container-lowest border-b border-outline-variant/20">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-error/70"></div>
              <div className="w-3 h-3 rounded-full bg-secondary/50"></div>
              <div className="w-3 h-3 rounded-full bg-tertiary/50"></div>
              <span className="ml-2 font-mono text-xs text-on-surface-variant">
                live_session_session_id_4492.kernel
              </span>
            </div>
            <div className="flex items-center space-x-3 text-xs font-mono">
              <span className="flex items-center text-secondary">
                <span className="w-2 h-2 rounded-full bg-secondary animate-ping mr-1.5"></span>
                BUFFER STREAMING
              </span>
              <span className="text-outline">|</span>
              <span className="text-on-surface-variant">
                LATENCY: <strong className="text-primary font-mono">142ms</strong>
              </span>
              <span className="text-outline">|</span>
              <span className="text-on-surface-variant">
                COHORT: <strong className="text-on-surface font-mono">SE-APAC-04</strong>
              </span>
            </div>
          </div>

          {/* Product Cockpit Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-outline-variant/20">
            {/* Left Console: Holographic Node & Question Context (5 Cols) */}
            <div className="lg:col-span-5 p-6 flex flex-col justify-between bg-surface-container-lowest/60 space-y-6">
              <div>
                {/* AI Agent Avatar Box */}
                <div className="relative rounded-xl p-6 bg-surface-container-low border border-outline-variant/20 flex flex-col items-center justify-center text-center overflow-hidden mb-6">
                  {/* Grid background overlay */}
                  <div className="absolute inset-0 opacity-10 bg-[linear-gradient(to_right,#808080_1px,transparent_1px),linear-gradient(to_bottom,#808080_1px,transparent_1px)] bg-[size:16px_16px]"></div>
                  
                  {/* Holographic Pulsing Avatar Core */}
                  <div className="relative w-28 h-28 mb-4 flex items-center justify-center">
                    <div className="absolute inset-0 rounded-full border border-secondary/30 animate-spin" style={{ animationDuration: '10s' }}></div>
                    <div className="absolute inset-2 rounded-full border border-primary/20 animate-spin" style={{ animationDuration: '6s', animationDirection: 'reverse' }}></div>
                    <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-primary to-secondary p-0.5 shadow-[0_0_30px_rgba(87,230,255,0.4)]">
                      <div className="w-full h-full bg-surface-container-lowest rounded-full flex items-center justify-center">
                        <span className="material-symbols-outlined text-secondary" style={{ fontSize: '28px' }}>
                          neurology
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="text-sm font-bold text-on-surface mb-0.5">IMAIRA Interview Node 01</div>
                  <div className="text-[10px] font-mono text-secondary tracking-wider mb-4">SYNTHETIC EVALUATOR ACTIVE</div>

                  {/* Live Waveform Frequency Visualizer */}
                  <div className="flex items-center space-x-1.5 h-10 py-1 mb-3">
                    <span className="w-1 bg-secondary rounded-full wave-bar"></span>
                    <span className="w-1 bg-secondary rounded-full wave-bar"></span>
                    <span className="w-1 bg-primary rounded-full wave-bar"></span>
                    <span className="w-1 bg-primary rounded-full wave-bar"></span>
                    <span className="w-1 bg-tertiary rounded-full wave-bar"></span>
                    <span className="w-1 bg-secondary rounded-full wave-bar"></span>
                    <span className="w-1 bg-primary rounded-full wave-bar"></span>
                    <span className="w-1 bg-secondary rounded-full wave-bar"></span>
                  </div>

                  <button
                    type="button"
                    onClick={handleToggleDemo}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-container-high border border-outline-variant/40 hover:border-secondary/60 text-secondary text-xs font-mono transition-colors"
                  >
                    <Volume2 size={13} />
                    <span>{isPlayingDemo ? 'Stop Speaking' : '🔊 Hear AI Question'}</span>
                  </button>
                </div>

                {/* Question Card */}
                <div className="rounded-xl p-4 bg-surface-container border border-outline-variant/30 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-primary uppercase font-semibold tracking-wider">
                      Active Evaluation Rubric #4
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-surface-container-high text-on-surface-variant">
                      L6 Dist-Sys
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-on-surface">Distributed Consensus: Partition Recovery</h3>
                  <p className="text-xs text-on-surface-variant leading-relaxed">
                    "Explain the Raft leader election mechanism when split-vote network partitions occur. Specifically address term index monotonicity and quorum re-establishment."
                  </p>
                </div>
              </div>

              {/* Dialect Invariant Check */}
              <div className="pt-4 border-t border-outline-variant/20 flex items-center justify-between text-xs font-mono">
                <span className="text-on-surface-variant">Decoupled Phonetic Filter:</span>
                <span className="inline-flex items-center text-secondary font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-secondary mr-1"></span>
                  PASSED (Zero Accent Penalty)
                </span>
              </div>
            </div>

            {/* Right Console: Transcript, Extraction & Semantic Telemetry (7 Cols) */}
            <div className="lg:col-span-7 p-6 flex flex-col justify-between bg-surface-container-low/40 space-y-6">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <span className="material-symbols-outlined text-secondary" style={{ fontSize: '18px' }}>
                      subtitles
                    </span>
                    <span className="text-sm font-bold text-on-surface">Phoneme-Agnostic Audio Ingestion</span>
                  </div>
                  <span className="px-2 py-1 rounded bg-surface-container-high text-xs font-mono text-secondary border border-outline-variant/20">
                    ASR Confidence: 99.4%
                  </span>
                </div>

                {/* Candidate Transcript with Verified Term Badges */}
                <div className="rounded-xl bg-surface-container-lowest p-4 border border-outline-variant/20 font-mono text-xs space-y-3 mb-6">
                  <div className="text-on-surface-variant">
                    <span className="text-outline">[00:14.2s] </span>
                    "When network partition happens, nodes in minority partition cannot reach quorum. So if leader lease expires, nodes initiate election with randomized timeouts. The candidate increments its{' '}
                    <span className="bg-secondary/15 text-secondary border border-secondary/30 px-1.5 py-0.5 rounded font-bold">
                      monotonic term index
                    </span>{' '}
                    and requests votes..."
                  </div>
                  <div className="text-on-surface-variant">
                    <span className="text-outline">[00:26.8s] </span>
                    "Even if candidate pronounces 'hash map' as 'has map' or 'Dijkstra' as 'die extra', the Stage 2 acoustic recovery aligns it against our 2,000-term glossary with{' '}
                    <span className="bg-primary/15 text-primary border border-primary/30 px-1.5 py-0.5 rounded font-bold">
                      zero fluency penalty
                    </span>
                    ."
                  </div>
                </div>

                {/* 3-Dimensional Decoupled Score Cards */}
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="p-3 bg-surface-container rounded-lg border border-outline-variant/20">
                    <div className="text-lg font-bold text-secondary">92.4%</div>
                    <div className="text-[10px] font-mono text-outline uppercase">Content (60%)</div>
                    <span className="text-[9px] text-secondary font-mono mt-1 block">Full Technical Credit</span>
                  </div>
                  <div className="p-3 bg-surface-container rounded-lg border border-outline-variant/20">
                    <div className="text-lg font-bold text-primary">88.5%</div>
                    <div className="text-[10px] font-mono text-outline uppercase">Structure (40%)</div>
                    <span className="text-[9px] text-primary font-mono mt-1 block">Framing & Closure</span>
                  </div>
                  <div className="p-3 bg-surface-container rounded-lg border border-outline-variant/20">
                    <div className="text-lg font-bold text-tertiary">91.0%</div>
                    <div className="text-[10px] font-mono text-outline uppercase">Delivery Diagnostics</div>
                    <span className="text-[9px] text-tertiary font-mono mt-1 block">0% Score Deduction</span>
                  </div>
                </div>
              </div>

              {/* Bottom Acoustic Telemetry Bar */}
              <div className="pt-4 border-t border-outline-variant/20 flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
                <span className="text-on-surface-variant flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-secondary text-sm">shield</span>
                  Acoustic Slice Recovery: Active (2,000 Terms)
                </span>
                <span className="text-secondary font-semibold">
                  Overall FairScore: 90.8% (Exemplary)
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* DUAL PERSPECTIVE TABS: STUDENT COACHING VS PLACEMENT OFFICER */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 space-y-6">
        <div className="text-center space-y-2">
          <span className="text-xs font-mono text-secondary uppercase tracking-wider font-semibold">
            Purpose-Built For Real Stakeholders
          </span>
          <h2 className="text-2xl sm:text-3xl font-bold text-on-surface">
            Who Benefits From IMAIRA FairScore?
          </h2>
          <p className="text-xs sm:text-sm text-on-surface-variant max-w-xl mx-auto">
            Switch views to explore how our evaluation architecture directly empowers candidates and campus placement leaders.
          </p>
        </div>

        <div className="flex justify-center gap-2">
          <button
            type="button"
            onClick={() => setActivePerspective('student')}
            className={`px-4 py-2 rounded-lg text-xs font-mono font-semibold transition-all ${
              activePerspective === 'student'
                ? 'bg-primary-container text-on-primary-container shadow-sm'
                : 'bg-surface-container text-on-surface-variant hover:text-on-surface border border-outline-variant/30'
            }`}
          >
            🎓 For Students & Candidates
          </button>
          <button
            type="button"
            onClick={() => setActivePerspective('officer')}
            className={`px-4 py-2 rounded-lg text-xs font-mono font-semibold transition-all ${
              activePerspective === 'officer'
                ? 'bg-secondary text-[#00363e] shadow-sm'
                : 'bg-surface-container text-on-surface-variant hover:text-on-surface border border-outline-variant/30'
            }`}
          >
            🏢 For Placement Officers & Colleges
          </button>
        </div>

        {activePerspective === 'student' ? (
          <div className="p-6 rounded-xl bg-surface-container-low border border-outline-variant/30 space-y-4">
            <div className="flex items-center gap-2 text-primary font-bold text-sm">
              <span className="material-symbols-outlined">school</span>
              <span>Speak Naturally in Your Accent. Build Real Interview Confidence.</span>
            </div>
            <p className="text-xs sm:text-sm text-on-surface-variant leading-relaxed">
              If you went to school in a Tamil, Kannada, Telugu, or Hindi medium, standard interview platforms mark your technical knowledge down just because you don't sound like a Silicon Valley native. IMAIRA FairScore guarantees that your content score depends 100% on what you explain, not how fluent you sound.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
              <div className="p-3 bg-surface-container rounded-lg border border-outline-variant/20 space-y-1">
                <span className="font-bold text-xs text-on-surface block">Zero Accent Penalties</span>
                <span className="text-[11px] text-on-surface-variant block">Pronunciation recoveries are diagnostic coaching points with 0.0 marks deducted.</span>
              </div>
              <div className="p-3 bg-surface-container rounded-lg border border-outline-variant/20 space-y-1">
                <span className="font-bold text-xs text-on-surface block">Timestamped Model Fixes</span>
                <span className="text-[11px] text-on-surface-variant block">Point directly to what concept was missing with actionable ≤30 word model fixes.</span>
              </div>
              <div className="p-3 bg-surface-container rounded-lg border border-outline-variant/20 space-y-1">
                <span className="font-bold text-xs text-on-surface block">Instant Re-Answer Loop</span>
                <span className="text-[11px] text-on-surface-variant block">Practice re-explaining the concept right inside the evaluation to recover marks on the spot.</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-6 rounded-xl bg-surface-container-low border border-outline-variant/30 space-y-4">
            <div className="flex items-center gap-2 text-secondary font-bold text-sm">
              <span className="material-symbols-outlined">analytics</span>
              <span>Differentiate True Technical Skill from Acoustic Tool Bias</span>
            </div>
            <p className="text-xs sm:text-sm text-on-surface-variant leading-relaxed">
              When student cohort averages drop on standard automated mock platforms, placement officers cannot tell if their students lack engineering knowledge or if the speech recognition tool failed on their accent. IMAIRA's Placement Officer Audit Tool provides mathematical evidence of fairness.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
              <div className="p-3 bg-surface-container rounded-lg border border-outline-variant/20 space-y-1">
                <span className="font-bold text-xs text-on-surface block">Tool vs. Skill Diagnostic</span>
                <span className="text-[11px] text-on-surface-variant block">Separates acoustic recovery rate from actual rubric mastery across student batches.</span>
              </div>
              <div className="p-3 bg-surface-container rounded-lg border border-outline-variant/20 space-y-1">
                <span className="font-bold text-xs text-on-surface block">Fairness Audit Log</span>
                <span className="text-[11px] text-on-surface-variant block">Live mathematical verification: |Δ| ≤ 5.0 pts across regional speaking styles.</span>
              </div>
              <div className="p-3 bg-surface-container rounded-lg border border-outline-variant/20 space-y-1">
                <span className="font-bold text-xs text-on-surface block">Exportable Audit Dossier</span>
                <span className="text-[11px] text-on-surface-variant block">Download full compliance and cohort analytics for campus placement records.</span>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* SYSTEM PIPELINE SECTION */}
      <section id="howItWorksSection" className="max-w-7xl mx-auto px-4 sm:px-6 space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <span className="text-xs font-mono uppercase tracking-wider text-secondary">
            System Pipeline
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-on-surface">
            An Evaluation Pipeline Built Around Fairness.
          </h2>
          <p className="text-xs sm:text-sm text-on-surface-variant">
            Five coordinated stages ensure objective, repeatable technical evaluations independent of acoustic surface variations.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {[
            { step: '01', title: 'Capture', desc: 'Continuous audio streaming via Web Audio API with client-side volume analysis.' },
            { step: '02', title: 'Transcribe', desc: 'Sub-second streaming recognition emitting provisional candidate hypotheses.' },
            { step: '03', title: 'Verify', desc: 'Stage 2 glossary alignment with 2,000 engineering terms and acoustic check.' },
            { step: '04', title: 'Evaluate', desc: 'Decoupled scoring for Content (60%), Structure (40%), and Delivery (0% penalty).' },
            { step: '05', title: 'Report', desc: 'Isotonic calibration, Dual Diagnosis, and instant Practice Re-Answer loop.' },
          ].map((item, idx) => (
            <div
              key={idx}
              className="p-4 bg-surface-container-low border border-outline-variant/20 rounded-xl space-y-2 hover:border-primary/50 transition-all shadow-sm"
            >
              <span className="w-7 h-7 rounded bg-surface-container-high text-primary font-mono font-bold text-xs flex items-center justify-center border border-outline-variant/30">
                {item.step}
              </span>
              <h4 className="text-sm font-bold text-on-surface">{item.title}</h4>
              <p className="text-xs text-on-surface-variant leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* FOOTER */}
      <footer className="max-w-7xl mx-auto px-4 sm:px-6 pt-10 border-t border-outline-variant/20 flex flex-col sm:flex-row justify-between items-center text-xs font-mono text-outline gap-4">
        <div>© 2026 IMAIRA FairScore • "Get Judged on Intelligence. Not Your Accent."</div>
        <div>Integraminds AI FRONTIER Software Track • Candidate Platform v4.2</div>
      </footer>
    </div>
  );
};
