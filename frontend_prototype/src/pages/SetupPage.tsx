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
  const [accentProfile, setAccentProfile] = useState('Indian English (Pan-Regional)');

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
      alert('Please test and verify your microphone before entering the interview.');
      return;
    }
    onStartSession({ name, domain, difficulty, numQuestions }, cameraStream);
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-surface-container-low border border-outline-variant/30 text-secondary mb-2">
          <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse"></span>
          <span>STAGE 0 // PRE-FLIGHT CONFIGURATION & HARDWARE CALIBRATION</span>
        </div>
        <h2 className="text-3xl font-extrabold text-on-surface tracking-tight">
          Configure Your Technical Interview
        </h2>
        <p className="text-xs text-on-surface-variant mt-1">
          Select your engineering domain, regional speaking profile, and verify microphone & camera hardware.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Top: AI Interviewer Avatar & Lip-Sync Verification */}
        <div className="md:col-span-2 bg-surface-container-low border border-outline-variant/30 rounded-xl p-6 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)] flex flex-col md:flex-row items-center gap-6">
          <div className="w-full md:w-56 shrink-0 flex justify-center">
            <HumanAvatar
              state={isAvatarSpeaking ? 'speaking' : 'idle'}
              statusText={isAvatarSpeaking ? 'Interviewer Speaking' : 'AI Interviewer Ready'}
              currentSpeechText={avatarGreeting}
            />
          </div>
          <div className="flex-1 space-y-3 text-left">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-primary/10 text-primary border border-primary/20">
                Virtual Human Interviewer
              </span>
              <span className="px-2 py-0.5 bg-secondary/10 text-secondary border border-secondary/30 text-[10px] font-mono font-bold rounded-full">
                Lip-Sync & Speech Synthesis Online
              </span>
            </div>
            <h3 className="text-lg font-bold text-on-surface">
              Meet Your AI Technical Interviewer
            </h3>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              Your AI interviewer interacts naturally via speech synthesis, lip-synchronization, and topic-grounded follow-ups. All evaluations run silently in the background with zero accent penalties.
            </p>
            <div className="pt-1 flex items-center gap-3">
              <button
                type="button"
                onClick={handleTestAvatarVoice}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-primary-container hover:bg-primary-fixed-dim text-on-primary-container rounded-lg text-xs font-mono font-bold shadow-sm transition-all"
              >
                <Volume2 size={14} />
                <span>{isAvatarSpeaking ? 'Stop Interviewer Voice' : '🔊 Test Interviewer Audio'}</span>
              </button>
              <span className="text-[11px] text-outline font-mono">
                Verifies speaker output before session starts
              </span>
            </div>
          </div>
        </div>

        {/* Left Column: Session Parameters */}
        <div className="bg-surface-container-low border border-outline-variant/30 rounded-xl p-6 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)] space-y-4">
          <h3 className="text-xs font-mono font-bold text-primary uppercase tracking-wider">
            1. Interview Parameters
          </h3>

          <div>
            <label className="block text-xs font-bold text-on-surface mb-1">
              Candidate Full Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full px-3 py-2 text-xs border border-outline-variant/30 rounded-lg text-on-surface focus:outline-none focus:ring-1 focus:ring-primary bg-surface-container"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-on-surface mb-1">
              Engineering Domain
            </label>
            <select
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-outline-variant/30 rounded-lg text-on-surface focus:outline-none focus:ring-1 focus:ring-primary bg-surface-container"
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

          <div>
            <label className="block text-xs font-bold text-on-surface mb-1">
              Regional Speaking Background (Vernacular Medium Safe)
            </label>
            <select
              value={accentProfile}
              onChange={(e) => setAccentProfile(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-outline-variant/30 rounded-lg text-on-surface focus:outline-none focus:ring-1 focus:ring-primary bg-surface-container"
            >
              <option value="Indian English (Pan-Regional)">Indian English (Pan-Regional / Code-Mixed)</option>
              <option value="Tamil-Medium English">Tamil-Medium Schooling Background</option>
              <option value="Telugu-Medium English">Telugu-Medium Schooling Background</option>
              <option value="Kannada-Medium English">Kannada-Medium Schooling Background</option>
              <option value="Hindi-Medium English">Hindi-Medium Schooling Background</option>
              <option value="International Standard English">International Standard English</option>
            </select>
            <span className="text-[10px] text-secondary font-mono block mt-1">
              🛡️ Full credit preserved regardless of pronunciation style.
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-on-surface mb-1">
                Difficulty Level
              </label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value as any)}
                className="w-full px-3 py-2 text-xs border border-outline-variant/30 rounded-lg text-on-surface focus:outline-none focus:ring-1 focus:ring-primary bg-surface-container"
              >
                <option value="Beginner">Beginner</option>
                <option value="Intermediate">Intermediate</option>
                <option value="Advanced">Advanced / Senior</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-on-surface mb-1">
                Questions
              </label>
              <select
                value={numQuestions}
                onChange={(e) => setNumQuestions(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs border border-outline-variant/30 rounded-lg text-on-surface focus:outline-none focus:ring-1 focus:ring-primary bg-surface-container"
              >
                <option value={2}>2 Questions</option>
                <option value={3}>3 Questions</option>
                <option value={5}>5 Questions</option>
              </select>
            </div>
          </div>
        </div>

        {/* Right Column: Hardware Checks & Integrity Disclosure */}
        <div className="bg-surface-container-low border border-outline-variant/30 rounded-xl p-6 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)] space-y-4">
          <h3 className="text-xs font-mono font-bold text-secondary uppercase tracking-wider">
            2. Hardware & Device Verification
          </h3>

          {/* Microphone Check */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-bold text-on-surface">Microphone (Required)</label>
              <button
                type="button"
                onClick={handleTestMic}
                disabled={isTestingMic}
                className={`px-3 py-1 text-xs font-mono font-semibold rounded-lg border transition-colors ${
                  micTested
                    ? 'bg-secondary/15 text-secondary border-secondary/40'
                    : 'bg-surface-container text-on-surface-variant border-outline-variant/40 hover:bg-surface-container-high'
                }`}
              >
                {micTested ? '✓ Microphone Verified' : 'Test Microphone 🎤'}
              </button>
            </div>
            <div className="w-full h-2 bg-surface-container-highest border border-outline-variant/20 rounded-full overflow-hidden">
              <div
                className="h-full bg-secondary transition-all duration-75"
                style={{ width: `${micVolume}%` }}
              />
            </div>
            <span className="text-[11px] text-outline font-mono block mt-1">
              {micTested
                ? 'Audio signal verified. Continuous acoustic streaming is ready.'
                : 'Click Test Microphone and speak a few words to calibrate noise floor.'}
            </span>
          </div>

          {/* Camera Check */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-bold text-on-surface">Camera (Optional)</label>
              <button
                type="button"
                onClick={handleTestCamera}
                disabled={cameraActive}
                className={`px-3 py-1 text-xs font-mono font-semibold rounded-lg border transition-colors ${
                  cameraActive
                    ? 'bg-primary/15 text-primary border-primary/40'
                    : 'bg-surface-container text-on-surface-variant border-outline-variant/40 hover:bg-surface-container-high'
                }`}
              >
                {cameraActive ? '✓ Camera Active' : 'Enable Camera 📷'}
              </button>
            </div>
            {cameraActive && (
              <span className="text-[11px] text-primary font-mono block">
                Camera feed verified. Gaze tracking and posture monitoring active.
              </span>
            )}
          </div>

          {/* On-Device Privacy Guarantee */}
          <div className="p-3.5 bg-surface-container rounded-lg border border-outline-variant/30 space-y-1 text-xs">
            <div className="flex items-center gap-1.5 text-secondary font-bold font-mono">
              <Shield size={14} />
              <span>On-Device Privacy & Raw Audio Policy:</span>
            </div>
            <p className="text-on-surface-variant leading-relaxed text-[11px]">
              Raw audio is automatically purged from the server after scoring. No voice recordings are retained unless the candidate explicitly opts in.
            </p>
          </div>

          {/* Submit Button */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={isRestricted}
              className="w-full py-3 px-4 bg-primary-container hover:bg-primary-fixed-dim text-on-primary-container font-bold rounded-lg text-xs font-mono shadow-[0_0_25px_rgba(108,136,255,0.4)] transition-all active:scale-[0.99] disabled:opacity-50"
            >
              {isRestricted ? 'Account Temporarily Restricted' : 'Enter Live Technical Interview Room →'}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
