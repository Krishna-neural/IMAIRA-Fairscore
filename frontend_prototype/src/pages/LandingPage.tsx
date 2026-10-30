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
  const demoText =
    "How do hash tables resolve collision, and what is the asymptotic difference between separate chaining and open addressing?";

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
    <div className="space-y-16 py-6">
      {/* Hero Section with Right-Side Realistic Product Preview */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
        <div className="lg:col-span-7 space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-50 text-blue-800 border border-blue-200 rounded-full text-xs font-semibold">
            Integraminds AI FRONTIER Software Track • Round 2 Candidate
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-[#101C35] tracking-tight leading-tight">
            Evaluate Knowledge. Not Accents.
          </h1>
          <p className="text-lg font-semibold text-[#2457A6]">
            Fair Technical Interview Evaluation for Global Engineering Teams
          </p>
          <p className="text-sm text-slate-600 leading-relaxed max-w-xl">
            An enterprise AI interview platform designed to evaluate technical competence, reasoning structure, and verbal clarity independently across diverse speaking styles, accents, and code-mixed speech.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <button
              onClick={onStartInterview}
              className="px-6 py-3 bg-[#2457A6] hover:bg-[#1A4482] text-white rounded font-bold text-sm shadow-sm transition-all"
            >
              Start an Interview
            </button>
            <button
              onClick={onExploreJudge}
              className="px-6 py-3 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded font-semibold text-sm transition-all"
            >
              Explore the Technology
            </button>
          </div>
        </div>

        {/* Right-Side Product Preview Card */}
        <div className="lg:col-span-5 bg-white border border-slate-200 rounded-lg shadow-lg overflow-hidden">
          <div className="bg-slate-50 border-b border-slate-200 px-4 py-2.5 flex items-center justify-between text-xs font-bold text-[#101C35]">
            <span className="uppercase tracking-wider">Live Assessment Session</span>
            <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px]">Session Active</span>
          </div>
          <div className="p-4 space-y-3.5 text-xs text-slate-700">
            {/* Interactive Human Avatar Preview */}
            <div className="flex justify-center">
              <HumanAvatar
                state={isPlayingDemo ? 'speaking' : 'idle'}
                statusText={isPlayingDemo ? 'AI Interviewer Speaking' : 'Virtual Interviewer Ready'}
                currentSpeechText={demoText}
              />
            </div>
            <div className="flex justify-center">
              <button
                type="button"
                onClick={handleToggleDemo}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-[#2457A6] border border-blue-200 rounded text-xs font-bold transition-colors"
              >
                <Volume2 size={13} />
                {isPlayingDemo ? 'Stop Voice Demo' : '🔊 Hear AI Interviewer Ask Question'}
              </button>
            </div>

            <div className="p-3 bg-blue-50/60 border border-blue-200 rounded space-y-1">
              <span className="font-bold text-blue-950 block">Candidate Spoken Response (Acoustically Verified):</span>
              <p className="text-slate-800">
                "We store key-value pairs in a <span className="bg-emerald-100 text-emerald-800 font-bold px-1 rounded">hash map</span> with linked lists for chaining..."
              </p>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="p-2 bg-slate-50 border border-slate-200 rounded">
                <div className="text-base font-extrabold text-[#2457A6]">88%</div>
                <div className="text-[10px] uppercase font-bold text-slate-500">Content (50%)</div>
              </div>
              <div className="p-2 bg-slate-50 border border-slate-200 rounded">
                <div className="text-base font-extrabold text-[#172846]">85%</div>
                <div className="text-[10px] uppercase font-bold text-slate-500">Structure (30%)</div>
              </div>
              <div className="p-2 bg-slate-50 border border-slate-200 rounded">
                <div className="text-base font-extrabold text-emerald-700">82%</div>
                <div className="text-[10px] uppercase font-bold text-slate-500">Fluency (20%)</div>
              </div>
            </div>
          </div>
          <div className="bg-blue-50/80 px-4 py-2 border-t border-blue-200 flex justify-between items-center text-[11px] text-blue-900 font-medium">
            <span>🛡️ Stage 2 Terminology Recovery: Verified</span>
            <span>Accent Invariance: |Δ| = 0.00 pts</span>
          </div>
        </div>
      </section>

      {/* Trust Indicators Bar */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-5 bg-white border border-slate-200 rounded-lg shadow-xs">
        <div className="border-r-0 lg:border-r border-slate-200 pr-4 space-y-1">
          <h4 className="text-sm font-bold text-[#101C35]">Accent-Aware Assessment</h4>
          <p className="text-xs text-slate-500">Tolerates Indian-English phonetics and code-mixed speech without scoring penalties.</p>
        </div>
        <div className="border-r-0 lg:border-r border-slate-200 pr-4 space-y-1">
          <h4 className="text-sm font-bold text-[#101C35]">Structured Evaluation</h4>
          <p className="text-xs text-slate-500">Decoupled scoring isolates technical mastery (50%), reasoning flow (30%), and fluency (20%).</p>
        </div>
        <div className="border-r-0 lg:border-r border-slate-200 pr-4 space-y-1">
          <h4 className="text-sm font-bold text-[#101C35]">Terminology Verification</h4>
          <p className="text-xs text-slate-500">2,000-term engineering glossary with RapidFuzz and Metaphone phonetic matching.</p>
        </div>
        <div className="space-y-1">
          <h4 className="text-sm font-bold text-[#101C35]">Transparent Feedback</h4>
          <p className="text-xs text-slate-500">Concise actionable fixes (≤30 words) with timestamped acoustic verification audit trail.</p>
        </div>
      </section>

      {/* Problem Comparison Section */}
      <section className="space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-[#2457A6]">The Evaluation Problem</span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#101C35]">Your Accent Shouldn't Define Your Technical Ability.</h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Standard speech recognition models systematically fail on regional accents and code-mixed speech, corrupting technical keywords and unfairly docking qualified candidates.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 bg-white border border-slate-200 border-t-4 border-t-red-500 rounded-lg shadow-xs space-y-3">
            <span className="text-xs font-bold uppercase text-red-600">Conventional Speech-to-Text</span>
            <h3 className="text-base font-bold text-[#101C35]">Acoustic Confusion & Unfair Deductions</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Standard models mishear non-native pronunciations of technical terms, mistaking acoustic ambiguity for candidate lack of knowledge.
            </p>
            <div className="p-3 bg-red-50 border border-red-200 rounded text-xs text-red-900 space-y-1 font-mono">
              <div><strong>Raw:</strong> "We store user profiles in a hash map..."</div>
              <div><strong>ASR:</strong> "We store user profiles in a <u>has map</u>..."</div>
              <div className="text-red-700 font-bold">Result: Deducted 15 marks for missing data structure</div>
            </div>
          </div>

          <div className="p-6 bg-white border border-slate-200 border-t-4 border-t-[#2457A6] rounded-lg shadow-xs space-y-3">
            <span className="text-xs font-bold uppercase text-[#2457A6]">IMAIRA FairScore Stage 2 Pipeline</span>
            <h3 className="text-base font-bold text-[#101C35]">Evidence-Checked Terminology Recovery</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              IMAIRA indexes 2,000+ technical terms, detects suspect spans, and acoustically verifies candidate phonemes with conservative abstention.
            </p>
            <div className="p-3 bg-blue-50 border border-blue-200 rounded text-xs text-blue-950 space-y-1 font-mono">
              <div><strong>Raw:</strong> "We store user profiles in a hash map..."</div>
              <div><strong>Stage 2:</strong> Matched "has map" → <span className="bg-emerald-100 text-emerald-800 font-bold px-1 rounded">hash map</span> (conf: 0.94)</div>
              <div className="text-emerald-700 font-bold">Result: Full marks awarded for hash table collision logic</div>
            </div>
          </div>
        </div>
      </section>

      {/* 5-Stage Pipeline Section */}
      <section id="howItWorksSection" className="space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-[#2457A6]">System Pipeline</span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#101C35]">An Evaluation Pipeline Built Around Fairness.</h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Five coordinated stages ensure objective, repeatable technical evaluations independent of acoustic surface variations.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {[
            { step: '01', title: 'Capture', desc: 'Continuous audio streaming via Web Audio API with client-side volume analysis.' },
            { step: '02', title: 'Transcribe', desc: 'Sub-second streaming recognition emitting provisional candidate hypotheses.' },
            { step: '03', title: 'Verify', desc: 'Stage 2 glossary alignment with RapidFuzz and Metaphone acoustic checks.' },
            { step: '04', title: 'Evaluate', desc: 'Decoupled scoring for Content (50%), Structure (30%), and Fluency (20%).' },
            { step: '05', title: 'Report', desc: 'Isotonic calibration, semantic rubric proposition tags, and coaching fixes.' },
          ].map((item, idx) => (
            <div key={idx} className="p-4 bg-white border border-slate-200 rounded-lg shadow-xs space-y-2 hover:border-[#2457A6] transition-all">
              <span className="w-7 h-7 rounded bg-blue-50 text-blue-800 font-bold text-xs flex items-center justify-center">
                {item.step}
              </span>
              <h4 className="text-sm font-bold text-[#101C35]">{item.title}</h4>
              <p className="text-xs text-slate-500 leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 3 Dimensions Section */}
      <section className="space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-[#2457A6]">Decoupled Criteria</span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#101C35]">Three Strictly Independent Dimensions</h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Unlike monolithic chatbots that penalize grammar, IMAIRA FairScore measures each dimension using isolated models.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 bg-white border border-slate-200 rounded-lg shadow-xs space-y-3">
            <span className="text-xs font-bold uppercase text-[#2457A6]">Dimension 1 • 50% Weight</span>
            <h3 className="text-lg font-bold text-[#101C35]">Content Mastery</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Evaluates factual engineering accuracy, cause-and-effect reasoning, and architectural depth against semantic rubric propositions (≥5 words).
            </p>
            <div className="p-2.5 bg-slate-50 border border-slate-200 rounded text-xs text-slate-700 font-medium">
              Invariant to surface vocabulary, speech pauses, and minor grammar variations.
            </div>
          </div>

          <div className="p-6 bg-white border border-slate-200 rounded-lg shadow-xs space-y-3">
            <span className="text-xs font-bold uppercase text-[#172846]">Dimension 2 • 30% Weight</span>
            <h3 className="text-lg font-bold text-[#101C35]">Structure & Coherence</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Analyzes logical argument progression: Framing (35% opening directness), Coherence (40% causal flow), and Closure (25% synthesis).
            </p>
            <div className="p-2.5 bg-slate-50 border border-slate-200 rounded text-xs text-slate-700 font-medium">
              Completely decoupled from pronunciation, accent cadence, and acoustic pitch.
            </div>
          </div>

          <div className="p-6 bg-white border border-slate-200 rounded-lg shadow-xs space-y-3">
            <span className="text-xs font-bold uppercase text-emerald-700">Dimension 3 • 20% Weight</span>
            <h3 className="text-lg font-bold text-[#101C35]">Communication Fluency</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Evaluates delivery pace (optimal 110–170 WPM), filler word frequency ("um", "like", "you know"), and extended hesitation pauses.
            </p>
            <div className="p-2.5 bg-slate-50 border border-slate-200 rounded text-xs text-slate-700 font-medium">
              Focuses strictly on conversational flow without penalizing regional intonation.
            </div>
          </div>
        </div>
      </section>

      {/* Corporate Footer */}
      <footer className="pt-10 border-t border-slate-200 flex flex-col sm:flex-row justify-between items-center text-xs text-slate-500 gap-4">
        <div>© 2026 IMAIRA FairScore • "Evaluate Knowledge. Not Accents."</div>
        <div>Integraminds AI FRONTIER Software Track • Round 2 Candidate</div>
      </footer>
    </div>
  );
};
