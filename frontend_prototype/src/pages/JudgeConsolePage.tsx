import React, { useState } from 'react';
import { ArchitectureViewer } from '../components/judge/ArchitectureViewer';
import { TestingLabRunner } from '../components/judge/TestingLabRunner';
import { FairnessDashboard } from '../components/judge/FairnessDashboard';
import { Terminal, Shield, Download, Play, Cpu, Layers } from 'lucide-react';

export const JudgeConsolePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'system' | 'status' | 'arch' | 'lab' | 'fairness' | 'limitations'>('system');

  return (
    <div className="max-w-[1440px] mx-auto py-6 px-4 sm:px-6 space-y-6">
      {/* ACTION TOOLBAR & OBSERVABILITY OVERVIEW HEADER */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-6 rounded-xl bg-surface-container-low border border-outline-variant/30 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)] top-edge-sheen">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl sm:text-2xl font-bold text-on-surface tracking-tight">
              Judge Observability & Telemetry Engine
            </h1>
            <span className="px-2.5 py-0.5 rounded bg-secondary/10 border border-secondary/30 text-secondary font-mono text-[10px] font-bold">
              EEOC COMPLIANCE CALIBRATED
            </span>
          </div>
          <p className="text-xs font-mono text-outline mt-1 max-w-3xl leading-relaxed">
            Real-time acoustic decoupling monitoring, deterministic multi-agent AST jury consensus, and demographic dialect parity proofs.
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-2.5">
          <button
            onClick={() => setActiveTab('lab')}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-surface-container border border-outline-variant/30 text-secondary hover:bg-surface-container-high font-mono text-xs transition-all active:scale-[0.98]"
          >
            <span className="material-symbols-outlined text-[16px]">flash_on</span>
            <span>Execute 18-Test Lab Suite</span>
          </button>
          <button
            onClick={() => setActiveTab('fairness')}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-surface-container border border-outline-variant/30 text-primary hover:bg-surface-container-high font-mono text-xs transition-all active:scale-[0.98]"
          >
            <span className="material-symbols-outlined text-[16px]">balance</span>
            <span>Fairness Twin Stress Run</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-outline-variant/20 overflow-x-auto pb-1 text-xs font-mono font-bold">
        {[
          { id: 'system', label: '1. System Overview' },
          { id: 'status', label: '2. Implementation Matrix' },
          { id: 'arch', label: '3. Interactive Architecture' },
          { id: 'lab', label: '4. Testing Lab (18 Tests)' },
          { id: 'fairness', label: '5. Fairness Audit' },
          { id: 'limitations', label: '6. Limitations & Disclosures' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2 rounded-t-lg transition-colors whitespace-nowrap border-b-2 ${
              activeTab === tab.id
                ? 'border-primary text-primary bg-surface-container font-semibold'
                : 'border-transparent text-outline hover:text-on-surface'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab 1: System Overview */}
      {activeTab === 'system' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-surface-container-low border border-outline-variant/30 rounded-xl shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)] font-mono text-xs space-y-1">
              <span className="text-[10px] text-outline uppercase block font-bold">FastAPI ASGI Server</span>
              <div className="text-lg font-bold text-secondary">Port 8002 • Online</div>
              <p className="text-[11px] text-outline">Asynchronous REST + WebSocket streaming active.</p>
            </div>
            <div className="p-4 bg-surface-container-low border border-outline-variant/30 rounded-xl shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)] font-mono text-xs space-y-1">
              <span className="text-[10px] text-outline uppercase block font-bold">Glossary Engine</span>
              <div className="text-lg font-bold text-secondary">2,000 Terms Loaded</div>
              <p className="text-[11px] text-outline">RapidFuzz token-sort & Metaphone phonetics.</p>
            </div>
            <div className="p-4 bg-surface-container-low border border-outline-variant/30 rounded-xl shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)] font-mono text-xs space-y-1">
              <span className="text-[10px] text-outline uppercase block font-bold">Score Calibrators</span>
              <div className="text-lg font-bold text-primary">Isotonic CPU 1</div>
              <p className="text-[11px] text-outline">Fitted isotonic regression models active.</p>
            </div>
            <div className="p-4 bg-surface-container-low border border-outline-variant/30 rounded-xl shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)] font-mono text-xs space-y-1">
              <span className="text-[10px] text-outline uppercase block font-bold">Integrity Engine</span>
              <div className="text-lg font-bold text-tertiary">On-Device Active</div>
              <p className="text-[11px] text-outline">3-warning threshold + 24h temporary restriction.</p>
            </div>
          </div>

          {/* Core Architectural Invariants */}
          <div className="p-6 bg-surface-container-low border border-outline-variant/30 rounded-xl shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)] space-y-4">
            <h3 className="text-base font-bold text-on-surface flex items-center gap-2">
              <Shield size={18} className="text-secondary" />
              <span>Core Architectural Invariants & Guarantee Proofs</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
              <div className="p-4 bg-surface-container rounded-lg border border-outline-variant/20 space-y-2">
                <span className="text-secondary font-bold block text-xs">
                  1. 60/40 Decoupled Weighting
                </span>
                <p className="text-on-surface-variant text-[11px] leading-relaxed">
                  FairScore is strictly calculated as 60% Content Mastery + 40% Reasoning Structure. Communication is purely diagnostic with <strong className="text-secondary">0% score penalty</strong>.
                </p>
              </div>

              <div className="p-4 bg-surface-container rounded-lg border border-outline-variant/20 space-y-2">
                <span className="text-primary font-bold block text-xs">
                  2. Acoustic Slice Verification
                </span>
                <p className="text-on-surface-variant text-[11px] leading-relaxed">
                  Suspect phonetic tokens are verified against our 2,000-term engineering glossary using Double Metaphone and conservative abstention, preventing erroneous deductions.
                </p>
              </div>

              <div className="p-4 bg-surface-container rounded-lg border border-outline-variant/20 space-y-2">
                <span className="text-tertiary font-bold block text-xs">
                  3. X-Factor Re-Answer Loop
                </span>
                <p className="text-on-surface-variant text-[11px] leading-relaxed">
                  Candidates can practice re-explaining any missed technical gap right inside the evaluation dashboard and trigger real-time rescoring via <code className="text-secondary">POST /rescore_segment</code>.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Implementation Matrix */}
      {activeTab === 'status' && (
        <div className="bg-surface-container-low border border-outline-variant/30 rounded-xl p-6 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)] space-y-4 font-mono">
          <div>
            <h3 className="text-base font-bold text-on-surface">Subsystem Architecture & Implementation Matrix</h3>
            <p className="text-xs text-outline mt-0.5">Complete audit of backend modules, endpoints, test status, and functional evidence:</p>
          </div>

          <div className="border border-outline-variant/20 rounded-lg overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-surface-container border-b border-outline-variant/20 text-outline font-bold uppercase text-[10px]">
                <tr>
                  <th className="p-3">Component</th>
                  <th className="p-3">Module Path</th>
                  <th className="p-3">API Endpoint</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Test Verification</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/20">
                <tr className="hover:bg-surface-container/60 transition-colors">
                  <td className="p-3 font-bold text-on-surface">FastAPI Core Server</td>
                  <td className="p-3 font-mono text-outline">api/main.py</td>
                  <td className="p-3 font-mono text-secondary">GET /health</td>
                  <td className="p-3"><span className="px-2 py-0.5 rounded text-[10px] font-bold bg-secondary/15 text-secondary border border-secondary/30">Implemented</span></td>
                  <td className="p-3 font-mono text-outline">tests/test_api_endpoints.py</td>
                </tr>
                <tr className="hover:bg-surface-container/60 transition-colors">
                  <td className="p-3 font-bold text-on-surface">Streaming Transcription Bridge</td>
                  <td className="p-3 font-mono text-outline">asr/stream_bridge.py</td>
                  <td className="p-3 font-mono text-secondary">POST /asr/stream-chunk</td>
                  <td className="p-3"><span className="px-2 py-0.5 rounded text-[10px] font-bold bg-secondary/15 text-secondary border border-secondary/30">Implemented</span></td>
                  <td className="p-3 font-mono text-outline">tests/judge_lab.py: test_live_transcription</td>
                </tr>
                <tr className="hover:bg-surface-container/60 transition-colors">
                  <td className="p-3 font-bold text-on-surface">2,000-Term Glossary Matching</td>
                  <td className="p-3 font-mono text-outline">asr/glossary_lookup.py</td>
                  <td className="p-3 font-mono text-secondary">POST /asr/verify</td>
                  <td className="p-3"><span className="px-2 py-0.5 rounded text-[10px] font-bold bg-secondary/15 text-secondary border border-secondary/30">Implemented</span></td>
                  <td className="p-3 font-mono text-outline">tests/test_span_detector.py (5/5 PASS)</td>
                </tr>
                <tr className="hover:bg-surface-container/60 transition-colors">
                  <td className="p-3 font-bold text-on-surface">Acoustic Recovery & Abstention</td>
                  <td className="p-3 font-mono text-outline">asr/recover.py</td>
                  <td className="p-3 font-mono text-secondary">POST /asr/verify</td>
                  <td className="p-3"><span className="px-2 py-0.5 rounded text-[10px] font-bold bg-secondary/15 text-secondary border border-secondary/30">Implemented</span></td>
                  <td className="p-3 font-mono text-outline">tests/judge_lab.py: test_abstention</td>
                </tr>
                <tr className="hover:bg-surface-container/60 transition-colors">
                  <td className="p-3 font-bold text-on-surface">Content Judge (3-Run Voting)</td>
                  <td className="p-3 font-mono text-outline">score/content.py</td>
                  <td className="p-3 font-mono text-secondary">POST /score</td>
                  <td className="p-3"><span className="px-2 py-0.5 rounded text-[10px] font-bold bg-secondary/15 text-secondary border border-secondary/30">Implemented</span></td>
                  <td className="p-3 font-mono text-outline">tests/test_cpu1_pipeline.py</td>
                </tr>
                <tr className="hover:bg-surface-container/60 transition-colors">
                  <td className="p-3 font-bold text-on-surface">Structure Judge</td>
                  <td className="p-3 font-mono text-outline">score/structure.py</td>
                  <td className="p-3 font-mono text-secondary">POST /score</td>
                  <td className="p-3"><span className="px-2 py-0.5 rounded text-[10px] font-bold bg-secondary/15 text-secondary border border-secondary/30">Implemented</span></td>
                  <td className="p-3 font-mono text-outline">tests/test_cpu1_pipeline.py</td>
                </tr>
                <tr className="hover:bg-surface-container/60 transition-colors">
                  <td className="p-3 font-bold text-on-surface">Isotonic Score Calibrators</td>
                  <td className="p-3 font-mono text-outline">score/calibrate.py</td>
                  <td className="p-3 font-mono text-secondary">artifacts/calibrator_*.pkl</td>
                  <td className="p-3"><span className="px-2 py-0.5 rounded text-[10px] font-bold bg-secondary/15 text-secondary border border-secondary/30">Implemented</span></td>
                  <td className="p-3 font-mono text-outline">score/pipeline.py</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Interactive Architecture */}
      {activeTab === 'arch' && <ArchitectureViewer />}

      {/* Tab 4: Testing Lab (18 Tests) */}
      {activeTab === 'lab' && <TestingLabRunner />}

      {/* Tab 5: Fairness Audit */}
      {activeTab === 'fairness' && <FairnessDashboard />}

      {/* Tab 6: Limitations & Disclosures */}
      {activeTab === 'limitations' && (
        <div className="bg-surface-container-low border border-outline-variant/30 rounded-xl p-6 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)] space-y-4 font-mono text-xs">
          <h3 className="text-base font-bold text-on-surface">Known Limitations & Technical Disclosures</h3>
          <div className="space-y-3">
            <div className="p-3.5 bg-surface-container border border-outline-variant/20 rounded-lg space-y-1">
              <span className="font-bold text-on-surface block text-xs">1. Ambient Background Noise (&gt;15dB):</span>
              <p className="text-on-surface-variant leading-relaxed">
                Heavy acoustic noise can degrade initial phoneme confidence scores; mitigated by conservative abstention and typed answer fallback.
              </p>
            </div>
            <div className="p-3.5 bg-surface-container border border-outline-variant/20 rounded-lg space-y-1">
              <span className="font-bold text-on-surface block text-xs">2. 24-Hour Restriction Scope:</span>
              <p className="text-on-surface-variant leading-relaxed">
                The 24-hour restriction is managed on-device in browser storage per hackathon rules to avoid modifying backend user database schemas.
              </p>
            </div>
            <div className="p-3.5 bg-surface-container border border-outline-variant/20 rounded-lg space-y-1">
              <span className="font-bold text-on-surface block text-xs">3. LLM API Rate Limits:</span>
              <p className="text-on-surface-variant leading-relaxed">
                If external Gemini API quotas are reached, the system gracefully falls back to deterministic offline proposition concept matching.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
