import React, { useState } from 'react';
import { Mic, Video, Shield, CheckCircle2, AlertCircle, Volume2 } from 'lucide-react';
import { audioService } from '../services/audioService';
import { speechService } from '../services/speechService';
import { HumanAvatar } from '../components/avatar/HumanAvatar';
import { CandidateConfig } from '../types/interview';

interface SetupPageProps {
  onStartSession: (config: CandidateConfig, cameraStream: MediaStream | null) => void;
  isRestricted: boolean;
}

export const SetupPage: React.FC<SetupPageProps> = ({ onStartSession, isRestricted }) => {
  const [name, setName] = useState('Candidate');
  const [domain, setDomain] = useState('Software and Computer Science Fundamentals');
  const [difficulty, setDifficulty] = useState<'Beginner' | 'Intermediate' | 'Advanced'>('Intermediate');
  const [numQuestions, setNumQuestions] = useState(3);

  // Hardware state
  const [micTested, setMicTested] = useState(false);
  const [micVolume, setMicVolume] = useState(0);
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [isTestingMic, setIsTestingMic] = useState(false);
  const [isAvatarSpeaking, setIsAvatarSpeaking] = useState(false);

  const avatarGreeting = `Hello ${name || 'Candidate'}! I am your AI technical interviewer today for ${domain}. I am listening clearly to your microphone and will evaluate your technical understanding with full accent fairness.`;

  const handleTestAvatarVoice = () => {
    if (isAvatarSpeaking) {
      speechService.setMuted(true);
      setIsAvatarSpeaking(false);
      setTimeout(() => speechService.setMuted(false), 200);
    } else {
      setIsAvatarSpeaking(true);
      speechService.speak(avatarGreeting, () => {
        setIsAvatarSpeaking(false);
      });
    }
  };

  const handleTestMic = async () => {
    setIsTestingMic(true);
    const ok = await audioService.startMicrophone((vol: number) => {
      setMicVolume(vol);
    });
    setIsTestingMic(false);
    if (ok) {
      setMicTested(true);
    } else {
      alert('Microphone access denied or unavailable. Please check your browser permissions.');
    }
  };

  const handleTestCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 } },
      });
      setCameraStream(stream);
      setCameraActive(true);
    } catch (err) {
      alert('Camera access denied or unavailable. Camera is optional.');
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!micTested) {
      alert('Please verify your microphone before entering the interview.');
      return;
    }
    onStartSession({ name, domain, difficulty, numQuestions }, cameraStream);
  };

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="mb-6">
        <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-800 border border-blue-200">
          Pre-Flight Configuration
        </span>
        <h2 className="text-2xl font-extrabold text-[#101C35] mt-1.5">
          Configure Your Technical Interview
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Select your engineering domain, target difficulty, and verify microphone & camera hardware.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Top Feature: AI Interviewer Avatar & Lip-Sync Verification */}
        <div className="md:col-span-2 bg-white border border-slate-200 rounded-lg p-5 shadow-xs flex flex-col md:flex-row items-center gap-6">
          <div className="w-full md:w-56 shrink-0 flex justify-center">
            <HumanAvatar
              state={isAvatarSpeaking ? 'speaking' : 'idle'}
              statusText={isAvatarSpeaking ? 'Interviewer Speaking' : 'AI Interviewer Ready'}
              currentSpeechText={avatarGreeting}
            />
          </div>
          <div className="flex-1 space-y-2.5 text-left">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-50 text-blue-800 border border-blue-200">
                Virtual Human Interviewer
              </span>
              <span className="px-2 py-0.5 bg-emerald-50 text-emerald-800 border border-emerald-200 text-[10px] font-bold rounded-full">
                Active Lip-Sync Engine
              </span>
            </div>
            <h3 className="text-base font-extrabold text-[#101C35]">
              Meet Your AI Technical Interviewer
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Your AI interviewer interacts naturally via speech synthesis, lip-synchronization, and eye contact. All evaluations run silently in the background without interrupting your responses.
            </p>
            <div className="pt-1 flex items-center gap-3">
              <button
                type="button"
                onClick={handleTestAvatarVoice}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#2457A6] hover:bg-[#1A4482] text-white rounded text-xs font-bold transition-colors"
              >
                <Volume2 size={14} />
                {isAvatarSpeaking ? 'Stop Interviewer Voice' : '🔊 Test Interviewer Voice & Lip-Sync'}
              </button>
              <span className="text-[11px] text-slate-500">
                Verifies speaker output & lip-sync before session starts
              </span>
            </div>
          </div>
        </div>

        {/* Left Column: Session Parameters */}
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs space-y-4">
          <h3 className="text-sm font-bold text-[#101C35] uppercase tracking-wide">
            Interview Parameters
          </h3>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Candidate Full Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-600 bg-white"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Engineering Domain
            </label>
            <select
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-600 bg-white"
            >
              <option value="Software and Computer Science Fundamentals">Software & Computer Science Fundamentals</option>
              <option value="Data Structures and Algorithms">Data Structures and Algorithms</option>
              <option value="System Design and Distributed Systems">System Design & Distributed Systems</option>
              <option value="Operating Systems and Concurrency">Operating Systems & Concurrency</option>
              <option value="Database Management Systems">Database Management Systems (DBMS)</option>
              <option value="Computer Networks and Protocols">Computer Networks & Protocols</option>
              <option value="Artificial Intelligence and Machine Learning">Artificial Intelligence & ML</option>
              <option value="Cybersecurity and Information Security">Cybersecurity & Security Engineering</option>
              <option value="Cloud Computing and DevOps">Cloud Computing & DevOps</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Difficulty Level
              </label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value as any)}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-600 bg-white"
              >
                <option value="Beginner">Beginner</option>
                <option value="Intermediate">Intermediate</option>
                <option value="Advanced">Advanced / Senior</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Questions
              </label>
              <select
                value={numQuestions}
                onChange={(e) => setNumQuestions(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-600 bg-white"
              >
                <option value={2}>2 Questions</option>
                <option value={3}>3 Questions</option>
                <option value={5}>5 Questions</option>
              </select>
            </div>
          </div>

          <div className="p-3 bg-blue-50/70 border border-blue-200 rounded text-xs text-blue-900 space-y-0.5">
            <span className="font-bold block text-blue-950">🔒 Anti-Manipulation Enforcement:</span>
            <p className="text-slate-600">
              Interviewer identity is permanently locked server-side. Evaluation is 100% deterministic and cannot be altered via prompt overrides.
            </p>
          </div>
        </div>

        {/* Right Column: Hardware Checks & Integrity Disclosure */}
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs space-y-4">
          <h3 className="text-sm font-bold text-[#101C35] uppercase tracking-wide">
            Hardware & Device Verification
          </h3>

          {/* Microphone Check */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-bold text-slate-700">Microphone (Required)</label>
              <button
                type="button"
                onClick={handleTestMic}
                disabled={isTestingMic}
                className={`px-2.5 py-1 text-xs font-semibold rounded border transition-colors ${
                  micTested
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                    : 'bg-slate-100 text-slate-700 border-slate-300 hover:bg-slate-200'
                }`}
              >
                {micTested ? '✓ Microphone Verified' : 'Test Microphone 🎤'}
              </button>
            </div>
            <div className="w-full h-2 bg-slate-100 border border-slate-300 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-600 transition-all duration-75"
                style={{ width: `${micVolume}%` }}
              />
            </div>
            <span className="text-[11px] text-slate-400 block mt-1">
              Captures continuous audio stream with sub-second provisional updates.
            </span>
          </div>

          {/* Camera Check */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-bold text-slate-700">Camera Preview (Optional)</label>
              <button
                type="button"
                onClick={handleTestCamera}
                className={`px-2.5 py-1 text-xs font-semibold rounded border transition-colors ${
                  cameraActive
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                    : 'bg-slate-100 text-slate-700 border-slate-300 hover:bg-slate-200'
                }`}
              >
                {cameraActive ? '✓ Camera Active' : 'Activate Camera 📹'}
              </button>
            </div>
            <div className="h-32 bg-slate-900 rounded overflow-hidden flex items-center justify-center border border-slate-300 relative">
              {cameraStream ? (
                <video
                  ref={(v) => {
                    if (v && cameraStream) {
                      v.srcObject = cameraStream;
                      v.play().catch(() => {});
                    }
                  }}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="text-xs text-slate-400 flex flex-col items-center gap-1">
                  <Video size={20} />
                  <span>Camera inactive (Click Activate to preview)</span>
                </div>
              )}
            </div>
          </div>

          {/* Integrity Monitoring Transparent Disclosure */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded text-xs space-y-1 text-slate-600">
            <span className="font-bold text-slate-800 flex items-center gap-1 text-[11px] uppercase">
              <Shield size={12} className="text-blue-700" />
              Integrity Monitoring Transparency:
            </span>
            <p>
              Session integrity monitoring runs on-device only. It checks solely for camera feed loss, obstruction, or multiple people in frame. No biometric identity recording, facial recognition, or emotion analysis is performed.
            </p>
          </div>

          <button
            type="submit"
            disabled={!micTested || isRestricted}
            className="w-full py-2.5 bg-[#2457A6] hover:bg-[#1A4482] text-white rounded font-bold text-sm shadow-xs transition-colors disabled:opacity-50"
          >
            {isRestricted ? 'Interviewer Restricted (24h)' : 'Begin Technical Interview'}
          </button>
        </div>
      </form>
    </div>
  );
};
