import React, { useState } from 'react';
import { HumanAvatar } from '../components/avatar/HumanAvatar';
import { speechService } from '../services/speechService';
import {
  Volume2,
  ShieldCheck,
  Award,
  Sparkles,
  Users,
  GraduationCap,
  Layers,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Zap,
  Globe,
  Lock,
} from 'lucide-react';

interface LandingPageProps {
  onStartInterview: () => void;
  onExploreJudge: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onStartInterview,
  onExploreJudge,
}) => {
  const [isPlayingDemo, setIsPlayingDemo] = useState(false);
  const [activeAudienceTab, setActiveAudienceTab] = useState<'students' | 'placement'>('students');
  const [simulatedMode, setSimulatedMode] = useState<'fairscore' | 'standard'>('fairscore');

  const demoQuestionText =
    "How do hash tables resolve collisions, and what is the asymptotic difference between separate chaining and open addressing?";

  const handleToggleDemo = () => {
    if (isPlayingDemo) {
      speechService.setMuted(true);
      setIsPlayingDemo(false);
      setTimeout(() => speechService.setMuted(false), 200);
    } else {
      setIsPlayingDemo(true);
      speechService.speak(demoQuestionText, () => {
        setIsPlayingDemo(false);
      });
    }
  };

  return (
    <div className="space-y-16 py-6 font-sans">
      {/* 1. Hero Section with Dual Action & Live Acoustic Simulator */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        <div className="lg:col-span-7 space-y-5">
          {/* Track Pill */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 bg-blue-50 text-[#1A4482] border border-blue-200 rounded-full text-xs font-bold shadow-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Integraminds AI FRONTIER Track • "Hear the Answer, Not the Accent"
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-[#101C35] tracking-tight leading-tight">
            Mock interviews that hear the <span className="text-[#2457A6]">answer</span>, not the <span className="text-slate-400 line-through">accent</span>.
          </h1>

          <p className="text-base sm:text-lg font-medium text-slate-700 leading-relaxed">
            Built for college students preparing for campus placements — especially first-generation graduates and students schooled in <strong>Tamil, Kannada, Telugu, or Hindi medium</strong>.
          </p>

          <p className="text-xs sm:text-sm text-slate-500 leading-relaxed max-w-xl">
            Monolithic AI interviewers penalize Indian accents, mishear non-native pronunciations like <em>"has map"</em> for <em>"hash map"</em>, and dock qualified candidates for hesitation. IMAIRA FairScore decouples <strong>Content (60%)</strong> from <strong>Structure (40%)</strong> with a <strong>0% Fluency Penalty</strong>, ensuring your genuine technical ability always shines through.
          </p>

          {/* Key Value Badges */}
          <div className="flex flex-wrap gap-2 pt-1 text-xs">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-full font-semibold">
              <ShieldCheck size={14} className="text-emerald-600" />
              0% Accent & Pause Penalty
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-50 text-blue-800 border border-blue-200 rounded-full font-semibold">
              <Sparkles size={14} className="text-blue-600" />
              2,000-Term Indian ASR Glossary
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-purple-50 text-purple-800 border border-purple-200 rounded-full font-semibold">
              <RotateCcw size={14} className="text-purple-600" />
              Interactive Re-Answer Practice
            </span>
          </div>

          {/* Primary Action Buttons */}
          <div className="flex flex-wrap gap-3 pt-3">
            <button
              onClick={onStartInterview}
              className="px-6 py-3.5 bg-[#2457A6] hover:bg-[#1A4482] text-white rounded-lg font-bold text-sm shadow-md hover:shadow-lg transition-all flex items-center gap-2 group"
            >
              <GraduationCap size={18} />
              <span>Start Practice Interview</span>
              <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
            </button>
            <button
              onClick={onExploreJudge}
              className="px-5 py-3.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-lg font-semibold text-sm shadow-xs transition-all flex items-center gap-2"
            >
              <Users size={16} className="text-slate-500" />
              <span>Placement Officer & Auditor Console</span>
            </button>
          </div>
        </div>

        {/* Right-Side Interactive Demo Card */}
        <div className="lg:col-span-5 bg-white border border-slate-200 rounded-xl shadow-lg overflow-hidden">
          <div className="bg-slate-900 text-white px-4 py-3 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-bold uppercase tracking-wider">Acoustic Fairness Comparison</span>
            </div>
            <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">
              Interactive Simulator
            </span>
          </div>

          <div className="p-4 space-y-3.5 text-xs">
            {/* Interactive Virtual Avatar Preview */}
            <div className="flex justify-center">
              <HumanAvatar
                state={isPlayingDemo ? 'speaking' : 'idle'}
                statusText={isPlayingDemo ? 'AI Interviewer Speaking...' : 'Virtual Technical Interviewer'}
                currentSpeechText={demoQuestionText}
              />
            </div>

            <div className="flex justify-center">
              <button
                type="button"
                onClick={handleToggleDemo}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-[#2457A6] border border-blue-200 rounded text-xs font-bold transition-colors"
              >
                <Volume2 size={14} />
                {isPlayingDemo ? 'Stop Audio Demo' : '🔊 Hear AI Interviewer Ask Technical Question'}
              </button>
            </div>

            {/* Toggle Comparison Mode */}
            <div className="flex bg-slate-100 p-1 rounded-lg border border-slate-200">
              <button
                onClick={() => setSimulatedMode('fairscore')}
                className={`flex-1 py-1.5 text-xs font-bold rounded-md transition-all ${
                  simulatedMode === 'fairscore'
                    ? 'bg-white text-[#2457A6] shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                ✨ IMAIRA FairScore (Our Model)
              </button>
              <button
                onClick={() => setSimulatedMode('standard')}
                className={`flex-1 py-1.5 text-xs font-bold rounded-md transition-all ${
                  simulatedMode === 'standard'
                    ? 'bg-white text-red-600 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                ⚠️ Standard AI Interviewer
              </button>
            </div>

            {/* Candidate Spoken Scenario */}
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1.5">
              <div className="flex items-center justify-between text-[11px]">
                <span className="font-bold text-slate-700">Candidate's Indian Spoken English:</span>
                <span className="text-[10px] text-slate-500 font-mono">Tamil/Hindi Native Speaker</span>
              </div>
              <p className="text-slate-900 font-mono text-[11px] bg-white p-2 rounded border border-slate-200">
                "Sir, for collision in our project we use{' '}
                <strong className={simulatedMode === 'fairscore' ? 'text-emerald-700 underline decoration-emerald-500' : 'text-red-600 underline decoration-red-500'}>
                  has map
                </strong>{' '}
                with chaining, and for container deployment we use{' '}
                <strong className={simulatedMode === 'fairscore' ? 'text-emerald-700 underline decoration-emerald-500' : 'text-red-600 underline decoration-red-500'}>
                  Kuber-netes
                </strong>
                ... um, space complexity is O(N)."
              </p>
            </div>

            {/* Comparison Result */}
            {simulatedMode === 'fairscore' ? (
              <div className="p-3 bg-emerald-50/80 border border-emerald-200 rounded-lg space-y-2 text-emerald-950">
                <div className="flex items-center justify-between">
                  <span className="font-bold flex items-center gap-1.5 text-xs text-emerald-900">
                    <CheckCircle2 size={15} className="text-emerald-600" />
                    Stage 2 Acoustic Recovery: Verified
                  </span>
                  <span className="text-[10px] bg-emerald-200 text-emerald-900 font-extrabold px-1.5 py-0.5 rounded">
                    Score: 88% (Pass)
                  </span>
                </div>
                <p className="text-[11px] text-emerald-800 leading-snug">
                  Phonetic engine recovers <strong>"hash map"</strong> and <strong>"Kubernetes"</strong> against 2,000-term glossary. Hesitation <em>"um"</em> is classified under delivery diagnostics with <strong>0 marks deducted</strong>. Full marks awarded for collision mechanics.
                </p>
              </div>
            ) : (
              <div className="p-3 bg-red-50/80 border border-red-200 rounded-lg space-y-2 text-red-950">
                <div className="flex items-center justify-between">
                  <span className="font-bold flex items-center gap-1.5 text-xs text-red-900">
                    <AlertTriangle size={15} className="text-red-600" />
                    Conventional Monolithic ASR Failure
                  </span>
                  <span className="text-[10px] bg-red-200 text-red-900 font-extrabold px-1.5 py-0.5 rounded">
                    Score: 35% (Fail)
                  </span>
                </div>
                <p className="text-[11px] text-red-800 leading-snug">
                  ASR mishears "has map" and drops "Kubernetes". Scorer docks <strong>-25 marks</strong> for missing data structure and <strong>-15 marks</strong> for speech pauses, unfairly rejecting a qualified candidate.
                </p>
              </div>
            )}

            {/* Accurate Decoupled Weights Grid */}
            <div className="grid grid-cols-3 gap-2 text-center pt-1">
              <div className="p-2 bg-blue-50/60 border border-blue-200 rounded">
                <div className="text-base font-extrabold text-[#2457A6]">60%</div>
                <div className="text-[10px] uppercase font-bold text-slate-600">Content Weight</div>
              </div>
              <div className="p-2 bg-slate-50 border border-slate-200 rounded">
                <div className="text-base font-extrabold text-[#172846]">40%</div>
                <div className="text-[10px] uppercase font-bold text-slate-600">Structure Weight</div>
              </div>
              <div className="p-2 bg-emerald-50 border border-emerald-200 rounded">
                <div className="text-base font-extrabold text-emerald-700">0%</div>
                <div className="text-[10px] uppercase font-bold text-emerald-800">Accent Penalty</div>
              </div>
            </div>
          </div>

          <div className="bg-slate-50 px-4 py-2.5 border-t border-slate-200 flex justify-between items-center text-[11px] text-slate-600 font-medium">
            <span>🛡️ Benchmark Invariance: |Δ| ≤ 5.0 pts</span>
            <span className="text-emerald-700 font-bold">Tested Across 5 Indian Accents</span>
          </div>
        </div>
      </section>

      {/* 2. Dual Audience Tab Switcher: For Students vs For Placement Officers */}
      <section className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-200 pb-4 gap-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-[#2457A6]">
              Who IMAIRA FairScore Serves
            </span>
            <h2 className="text-2xl font-extrabold text-[#101C35] mt-1">
              Designed for Campus Hiring Realities
            </h2>
          </div>
          <div className="flex bg-slate-100 p-1 rounded-lg border border-slate-200">
            <button
              onClick={() => setActiveAudienceTab('students')}
              className={`px-4 py-2 rounded-md text-xs font-bold transition-all flex items-center gap-1.5 ${
                activeAudienceTab === 'students'
                  ? 'bg-white text-[#2457A6] shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <GraduationCap size={15} />
              <span>For Students & Job Seekers</span>
            </button>
            <button
              onClick={() => setActiveAudienceTab('placement')}
              className={`px-4 py-2 rounded-md text-xs font-bold transition-all flex items-center gap-1.5 ${
                activeAudienceTab === 'placement'
                  ? 'bg-white text-[#2457A6] shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Users size={15} />
              <span>For Placement Officers & Evaluators</span>
            </button>
          </div>
        </div>

        {activeAudienceTab === 'students' ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-5 bg-blue-50/50 border border-blue-200 rounded-lg space-y-2.5">
              <div className="w-8 h-8 rounded bg-blue-100 text-[#2457A6] flex items-center justify-center font-bold">
                01
              </div>
              <h3 className="text-sm font-bold text-[#101C35]">Speak Freely in Your Natural Voice</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                You do not need to fake an American or British accent. Whether you speak Indian English with Tamil, Telugu, Kannada, or Hindi cadence, our acoustic slice verification maps your pronunciation accurately.
              </p>
            </div>
            <div className="p-5 bg-emerald-50/50 border border-emerald-200 rounded-lg space-y-2.5">
              <div className="w-8 h-8 rounded bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold">
                02
              </div>
              <h3 className="text-sm font-bold text-[#101C35]">Zero Hesitation Penalties</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Take your time to structure your thoughts. Extended pauses or conversational filler words ("um", "like") are provided as gentle delivery feedback and will <strong>never decrease your technical score</strong>.
              </p>
            </div>
            <div className="p-5 bg-purple-50/50 border border-purple-200 rounded-lg space-y-2.5">
              <div className="w-8 h-8 rounded bg-purple-100 text-purple-800 flex items-center justify-center font-bold">
                03
              </div>
              <h3 className="text-sm font-bold text-[#101C35]">Interactive Re-Answer Practice</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Receive model sentence fixes (≤30 words) with exact timestamps. Hit <strong>"Practice Re-Answer"</strong> to re-speak the missing concept and instantly recover lost marks on your scorecard.
              </p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-5 bg-slate-50 border border-slate-200 rounded-lg space-y-2.5">
              <div className="w-8 h-8 rounded bg-slate-200 text-slate-800 flex items-center justify-center font-bold">
                01
              </div>
              <h3 className="text-sm font-bold text-[#101C35]">Distinguish Skill Gaps from Tool Bias</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Placement officers cannot tell whether a low cohort average is about skill or about the tool. IMAIRA FairScore proves with mathematical certainty that low scores reflect missing technical concepts, not pronunciation.
              </p>
            </div>
            <div className="p-5 bg-blue-50/50 border border-blue-200 rounded-lg space-y-2.5">
              <div className="w-8 h-8 rounded bg-blue-100 text-[#2457A6] flex items-center justify-center font-bold">
                02
              </div>
              <h3 className="text-sm font-bold text-[#101C35]">Cross-Accent Benchmark Audit</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Verified compliance with Integraminds Round 2 requirements: the same answer spoken by speakers with different regional accents varies by <strong>no more than 5.0 points out of 100</strong>.
              </p>
            </div>
            <div className="p-5 bg-emerald-50/50 border border-emerald-200 rounded-lg space-y-2.5">
              <div className="w-8 h-8 rounded bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold">
                03
              </div>
              <h3 className="text-sm font-bold text-[#101C35]">Auditable Terminology Logs</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Inspect millisecond-level acoustic slices for every technical keyword (RapidFuzz + Double Metaphone phonetic recovery). Download comprehensive cohort reports for college placement drives.
              </p>
            </div>
          </div>
        )}
      </section>

      {/* 3. Three Independent Evaluation Dimensions (Accurate Decoupled Weights) */}
      <section className="space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-[#2457A6]">
            Transparent Scoring Architecture
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#101C35]">
            Three Strictly Decoupled Evaluation Dimensions
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Unlike standard AI bots that blend vocabulary and grammar into a single biased number, IMAIRA FairScore measures each dimension independently.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Dimension 1: Content (60%) */}
          <div className="p-6 bg-white border border-slate-200 border-t-4 border-t-[#2457A6] rounded-xl shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase text-[#2457A6]">Dimension 1</span>
              <span className="px-2 py-0.5 bg-blue-100 text-[#1A4482] rounded text-[11px] font-extrabold">
                60% Total Weight
              </span>
            </div>
            <h3 className="text-lg font-bold text-[#101C35]">Content Mastery</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Evaluates factual engineering accuracy, algorithmic mechanisms, and architectural tradeoffs against semantic rubric propositions (≥5 words).
            </p>
            <div className="p-2.5 bg-blue-50/60 border border-blue-200 rounded text-xs text-blue-950 font-medium">
              🛡️ Invariant to regional accents, speaking pauses, and minor grammar variations.
            </div>
          </div>

          {/* Dimension 2: Structure (40%) */}
          <div className="p-6 bg-white border border-slate-200 border-t-4 border-t-[#172846] rounded-xl shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase text-[#172846]">Dimension 2</span>
              <span className="px-2 py-0.5 bg-slate-200 text-slate-800 rounded text-[11px] font-extrabold">
                40% Total Weight
              </span>
            </div>
            <h3 className="text-lg font-bold text-[#101C35]">Structure & Coherence</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Measures logical argument progression: Framing (35% direct opening), Coherence (40% causal progression), and Closure (25% architectural synthesis).
            </p>
            <div className="p-2.5 bg-slate-50 border border-slate-200 rounded text-xs text-slate-700 font-medium">
              🛡️ Decoupled from native pronunciation cadence, speech rate, and acoustic pitch.
            </div>
          </div>

          {/* Dimension 3: Delivery Diagnostics (0% Penalty) */}
          <div className="p-6 bg-white border border-slate-200 border-t-4 border-t-emerald-600 rounded-xl shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase text-emerald-700">Dimension 3</span>
              <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded text-[11px] font-extrabold">
                0% Score Penalty
              </span>
            </div>
            <h3 className="text-lg font-bold text-[#101C35]">Delivery & Articulation Diagnostics</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Analyzes speaking pace (optimal 110–170 WPM), hesitation duration, and filler word frequency solely as actionable coaching tips.
            </p>
            <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded text-xs text-emerald-900 font-semibold">
              ✓ 0.0 marks deducted. First-generation graduates are never penalized for delivery style.
            </div>
          </div>
        </div>
      </section>

      {/* 4. 5-Stage System Pipeline Section */}
      <section id="howItWorksSection" className="space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-[#2457A6]">
            Engineering Pipeline
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#101C35]">
            How IMAIRA FairScore Evaluates Technical Answers
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Five coordinated stages ensure objective, repeatable technical evaluations independent of acoustic surface variations.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
          {[
            {
              step: '01',
              title: 'Continuous Capture',
              desc: 'Continuous Web Audio API recording with client-side decibel levels. No word or duration cutoff.',
            },
            {
              step: '02',
              title: 'Sub-Second Stream',
              desc: 'Streaming speech recognition emitting real-time provisional candidate hypotheses.',
            },
            {
              step: '03',
              title: 'Acoustic Verification',
              desc: 'Stage 2 glossary alignment with RapidFuzz and Metaphone phonetic matching with conservative abstention.',
            },
            {
              step: '04',
              title: 'Decoupled Scoring',
              desc: 'Separate scoring for Content (60%) and Structure (40%) with Isotonic Calibration to human rubrics.',
            },
            {
              step: '05',
              title: 'Re-Answer Coaching',
              desc: 'Time-linked actionable fixes (≤30 words) with interactive instant re-answer rescoring loop.',
            },
          ].map((item, idx) => (
            <div
              key={idx}
              className="p-4 bg-white border border-slate-200 rounded-lg shadow-xs space-y-2 hover:border-[#2457A6] hover:shadow-md transition-all group"
            >
              <span className="w-8 h-8 rounded-lg bg-blue-50 text-[#2457A6] font-extrabold text-xs flex items-center justify-center group-hover:bg-[#2457A6] group-hover:text-white transition-colors">
                {item.step}
              </span>
              <h4 className="text-sm font-bold text-[#101C35]">{item.title}</h4>
              <p className="text-xs text-slate-500 leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 5. Student Reassurance Banner */}
      <section className="bg-gradient-to-r from-blue-900 to-[#101C35] text-white rounded-xl p-8 shadow-md">
        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-800/60 border border-blue-700 rounded-full text-xs font-semibold text-blue-200">
            <Lock size={13} />
            Student Privacy & Anti-Bias Commitment
          </div>
          <h3 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Ready to practice your placement interview without fear?
          </h3>
          <p className="text-xs sm:text-sm text-blue-200 leading-relaxed">
            Your audio is processed purely for technical keyword verification and is automatically deleted upon session conclusion. Zero facial emotion scoring, zero accent deductions, and 100% focus on engineering concepts.
          </p>
          <div className="pt-2">
            <button
              onClick={onStartInterview}
              className="px-6 py-3 bg-white hover:bg-slate-100 text-[#101C35] rounded-lg font-bold text-sm shadow-sm transition-all"
            >
              Launch Practice Interview Session →
            </button>
          </div>
        </div>
      </section>

      {/* Corporate Footer */}
      <footer className="pt-8 border-t border-slate-200 flex flex-col sm:flex-row justify-between items-center text-xs text-slate-500 gap-4">
        <div>© 2026 IMAIRA FairScore • Integraminds AI FRONTIER Track</div>
        <div className="flex items-center gap-4">
          <span>Targeted for Tamil, Kannada, Telugu & Hindi Medium Engineers</span>
          <button onClick={onExploreJudge} className="text-[#2457A6] font-semibold hover:underline">
            Audit Documentation ↗
          </button>
        </div>
      </footer>
    </div>
  );
};
