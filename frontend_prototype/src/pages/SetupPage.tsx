import React, { useState } from 'react';
import {
  Mic,
  Video,
  Shield,
  CheckCircle2,
  AlertCircle,
  Volume2,
  Sparkles,
  HeartHandshake,
  GraduationCap,
  Globe,
  Radio,
} from 'lucide-react';
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
  const [regionalAccent, setRegionalAccent] = useState('General Indian English (Pan-India)');

  // Hardware state
  const [micTested, setMicTested] = useState(false);
  const [micVolume, setMicVolume] = useState(0);
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [isTestingMic, setIsTestingMic] = useState(false);
  const [isAvatarSpeaking, setIsAvatarSpeaking] = useState(false);

  const avatarGreeting = `Hello ${name || 'Candidate'}! I am your AI technical interviewer for ${domain}. Please speak naturally in your normal speaking accent. Our acoustic verification will protect your technical answers with zero accent penalties. Whenever you are ready, let's begin!`;

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
      if (vol > 15) {
        setMicTested(true);
      }
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
      alert('Camera access denied or unavailable. Camera is optional for integrity monitoring.');
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!micTested) {
      alert('Please test your microphone before entering the interview so we can verify audio levels.');
      return;
    }
    // Set speech service language to Indian English by default
    speechService.setLanguage('en-IN');
    onStartSession({ name, domain, difficulty, numQuestions }, cameraStream);
  };

  return (
    <div className="max-w-4xl mx-auto py-6 space-y-6 font-sans">
      {/* Student Encouragement Banner */}
      <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-emerald-50 border border-blue-200 rounded-xl p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-[#2457A6] text-white">
              Student Preparation Portal
            </span>
            <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
              Zero Accent Penalty Active
            </span>
          </div>
          <h2 className="text-xl sm:text-2xl font-black text-[#101C35]">
            Configure Your Placement Practice Session
          </h2>
          <p className="text-xs text-slate-600 leading-relaxed">
            Take a deep breath! Speak in whatever pace is comfortable for you. Pauses to think will <strong>never</strong> lower your technical score.
          </p>
        </div>
        <div className="shrink-0 flex items-center gap-2 text-xs font-semibold text-slate-700 bg-white/80 p-2.5 rounded-lg border border-slate-200 shadow-xs">
          <HeartHandshake className="text-[#2457A6]" size={20} />
          <span>Vernacular Medium Friendly</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Top Feature: Meet Your AI Technical Interviewer */}
        <div className="md:col-span-2 bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col md:flex-row items-center gap-6">
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
                Interactive Lip-Sync Avatar
              </span>
              <span className="px-2 py-0.5 bg-emerald-50 text-emerald-800 border border-emerald-200 text-[10px] font-bold rounded-full">
                Real-Time Audio Synthesis
              </span>
            </div>
            <h3 className="text-base font-extrabold text-[#101C35]">
              Meet Your Virtual Technical Interviewer
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Your AI interviewer will ask questions by voice and listen patiently. You can speak as long as you need, replay any question at any time, or type formulas and code if you prefer.
            </p>
            <div className="pt-1 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={handleTestAvatarVoice}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-[#2457A6] hover:bg-[#1A4482] text-white rounded-lg text-xs font-bold transition-all shadow-xs"
              >
                <Volume2 size={14} />
                {isAvatarSpeaking ? 'Stop Voice Playback' : '🔊 Test Interviewer Voice & Audio'}
              </button>
              <span className="text-[11px] text-slate-500">
                Ensures your speakers/headphones are functioning clearly
              </span>
            </div>
          </div>
        </div>

        {/* Left Column: Candidate & Interview Parameters */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100 pb-2">
            1. Candidate & Domain Profile
          </h3>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Candidate Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Ramesh Kumar"
              required
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-[#2457A6] bg-white transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1 flex items-center justify-between">
              <span>Technical Domain</span>
              <span className="text-[10px] font-medium text-blue-700">Aligned with Campus Placement Syllabi</span>
            </label>
            <select
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-[#2457A6] bg-white transition-all cursor-pointer"
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

          {/* Regional Dialect Respect Selector */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1 flex items-center justify-between">
              <span className="flex items-center gap-1">
                <Globe size={13} className="text-[#2457A6]" />
                Regional Accent Profile (For ASR Adaptation)
              </span>
              <span className="text-[10px] text-emerald-700 font-bold">Never penalized</span>
            </label>
            <select
              value={regionalAccent}
              onChange={(e) => setRegionalAccent(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-[#2457A6] bg-white transition-all cursor-pointer"
            >
              <option value="Tamil-influenced English (South Zone)">🇮🇳 Tamil-influenced English (South Zone)</option>
              <option value="Telugu-influenced English (South Zone)">🇮🇳 Telugu-influenced English (South Zone)</option>
              <option value="Kannada-influenced English (South Zone)">🇮🇳 Kannada-influenced English (South Zone)</option>
              <option value="Hindi-influenced English (North/Central Zone)">🇮🇳 Hindi-influenced English (North/Central Zone)</option>
              <option value="General Indian English (Pan-India)">🇮🇳 General Indian English (Pan-India)</option>
              <option value="Standard International English">🌐 Standard International English</option>
            </select>
            <span className="text-[10px] text-slate-500 mt-1 block">
              Informs Stage 2 acoustic slice recovery to calibrate phonetic tolerances for your native tongue.
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Target Difficulty
              </label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value as any)}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-[#2457A6] bg-white transition-all cursor-pointer"
              >
                <option value="Beginner">Entry Level / Freshman</option>
                <option value="Intermediate">Campus Placement (Intermediate)</option>
                <option value="Advanced">Advanced / Product Company</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Interview Questions
              </label>
              <select
                value={numQuestions}
                onChange={(e) => setNumQuestions(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-[#2457A6] bg-white transition-all cursor-pointer"
              >
                <option value={2}>2 Questions (~5 mins)</option>
                <option value={3}>3 Questions (~8 mins)</option>
                <option value={5}>5 Questions (~15 mins)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Right Column: Hardware Checks & Integrity Disclosure */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100 pb-2">
            2. Audio & Hardware Check
          </h3>

          {/* Microphone Check with Interactive Level Meter */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                <Mic size={14} className="text-[#2457A6]" />
                <span>Microphone (Required)</span>
              </label>
              <button
                type="button"
                onClick={handleTestMic}
                disabled={isTestingMic}
                className={`px-3 py-1 text-xs font-bold rounded-lg border transition-all ${
                  micTested
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                    : 'bg-blue-50 text-[#2457A6] border-blue-200 hover:bg-blue-100'
                }`}
              >
                {micTested ? '✓ Microphone Verified' : 'Click to Test Microphone'}
              </button>
            </div>

            {/* Level Meter Bar */}
            <div className="w-full h-3 bg-slate-100 border border-slate-200 rounded-full overflow-hidden p-0.5">
              <div
                className={`h-full rounded-full transition-all duration-100 ${
                  micVolume > 20 ? 'bg-emerald-500' : micVolume > 5 ? 'bg-blue-500' : 'bg-slate-300'
                }`}
                style={{ width: `${Math.min(100, Math.max(8, micVolume))}%` }}
              />
            </div>

            <div className="flex items-center justify-between text-[11px] text-slate-500">
              <span>{micTested ? '🟢 Live sound detection active' : 'Speak into mic to calibrate levels'}</span>
              <span className="font-mono text-slate-700">{micVolume > 0 ? `${Math.round(micVolume)}% vol` : 'Standby'}</span>
            </div>

            <p className="text-[11px] text-slate-500 bg-slate-50 p-2 rounded border border-slate-200">
              💡 <em>Say "hash map and binary tree" into your microphone to verify acoustic response.</em>
            </p>
          </div>

          {/* Camera Check (Optional) */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                <Video size={14} className="text-slate-500" />
                <span>Camera Preview (100% Optional)</span>
              </label>
              <button
                type="button"
                onClick={handleTestCamera}
                className={`px-3 py-1 text-xs font-bold rounded-lg border transition-all ${
                  cameraActive
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                    : 'bg-slate-100 text-slate-700 border-slate-300 hover:bg-slate-200'
                }`}
              >
                {cameraActive ? '✓ Camera Active' : 'Enable Camera (Optional)'}
              </button>
            </div>

            <div className="h-28 bg-slate-900 rounded-lg overflow-hidden flex items-center justify-center border border-slate-300 relative">
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
                <div className="text-xs text-slate-400 flex flex-col items-center gap-1 p-3 text-center">
                  <Video size={18} className="text-slate-500" />
                  <span>Camera is optional. Your interview will proceed smoothly even without a webcam.</span>
                </div>
              )}
            </div>
          </div>

          {/* Transparent Integrity Disclosure */}
          <div className="p-3 bg-blue-50/50 border border-blue-200 rounded-lg text-xs space-y-1 text-slate-600">
            <span className="font-bold text-[#101C35] flex items-center gap-1 text-[11px]">
              <Shield size={13} className="text-[#2457A6]" />
              Privacy & On-Device Monitoring Guarantee:
            </span>
            <p className="text-[11px] leading-relaxed text-slate-600">
              Integrity monitoring runs locally on your browser. No biometric identification, eye-gaze tracking, or emotion surveillance is performed. Your voice audio is automatically deleted immediately after the interview.
            </p>
          </div>

          <button
            type="submit"
            disabled={!micTested || isRestricted}
            className="w-full py-3 bg-[#2457A6] hover:bg-[#1A4482] text-white rounded-lg font-bold text-sm shadow-md transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <GraduationCap size={16} />
            <span>{isRestricted ? 'Session Restricted' : 'Enter Interview Room'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
