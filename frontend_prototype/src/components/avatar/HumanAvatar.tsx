import React, { useEffect, useState, useRef } from 'react';
import { Volume2, VolumeX, RotateCcw, MessageSquare } from 'lucide-react';
import { speechService } from '../../services/speechService';

interface HumanAvatarProps {
  state: 'idle' | 'speaking' | 'listening' | 'processing';
  statusText?: string;
  currentSpeechText?: string;
  onReplayQuestion?: () => void;
  showCaptionsDefault?: boolean;
}

export const HumanAvatar: React.FC<HumanAvatarProps> = ({
  state,
  statusText,
  currentSpeechText = '',
  onReplayQuestion,
  showCaptionsDefault = true,
}) => {
  const [mouthOpen, setMouthOpen] = useState(false);
  const [mouthViseme, setMouthViseme] = useState(0); // 0 = closed, 1 = slight, 2 = wide, 3 = round, 4 = smile open
  const [isBlinking, setIsBlinking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [showCaptions, setShowCaptions] = useState(showCaptionsDefault);

  // Lip-sync listener from speechService
  useEffect(() => {
    speechService.onMouthMovement((isOpen, viseme) => {
      setMouthOpen(isOpen);
      setMouthViseme(viseme);
    });
  }, []);

  // Natural periodic eye blinking (every 3.5 to 5.5 seconds)
  useEffect(() => {
    const blinkInterval = setInterval(() => {
      setIsBlinking(true);
      setTimeout(() => setIsBlinking(false), 160); // standard human blink duration ~150ms
    }, 4000 + Math.random() * 2000);

    return () => clearInterval(blinkInterval);
  }, []);

  const handleToggleMute = () => {
    const nextMuted = !isMuted;
    setIsMuted(nextMuted);
    speechService.setMuted(nextMuted);
  };

  const handleReplay = () => {
    if (onReplayQuestion) {
      onReplayQuestion();
    } else if (currentSpeechText) {
      speechService.speak(currentSpeechText);
    }
  };

  return (
    <div className="flex flex-col items-center w-full max-w-sm bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
      {/* Avatar Stage Window */}
      <div className="relative w-full h-64 bg-gradient-to-b from-slate-100 to-slate-200 flex items-center justify-center overflow-hidden border-b border-slate-200">
        {/* Realistic Virtual Human Vector Rendering */}
        <svg
          viewBox="0 0 200 240"
          className={`w-48 h-56 transition-transform duration-300 ${
            state === 'speaking'
              ? 'animate-subtle-sway'
              : state === 'listening'
              ? 'scale-105'
              : ''
          }`}
          style={{ filter: 'drop-shadow(0 4px 6px rgba(16, 28, 53, 0.08))' }}
        >
          <defs>
            <linearGradient id="skinGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#F5D0B5" />
              <stop offset="100%" stopColor="#E6B898" />
            </linearGradient>
            <linearGradient id="hairGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#2D3748" />
              <stop offset="100%" stopColor="#1A202C" />
            </linearGradient>
            <linearGradient id="suitGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#1E293B" />
              <stop offset="100%" stopColor="#0F172A" />
            </linearGradient>
            <linearGradient id="shirtGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#FFFFFF" />
              <stop offset="100%" stopColor="#E2E8F0" />
            </linearGradient>
            <linearGradient id="tieGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#2563EB" />
              <stop offset="100%" stopColor="#1D4ED8" />
            </linearGradient>
          </defs>

          {/* Torso: Professional Navy Suit & Collared Shirt */}
          <path d="M 40 240 C 40 185, 75 175, 100 175 C 125 175, 160 185, 160 240 Z" fill="url(#suitGrad)" />
          {/* Inner Collared Shirt */}
          <polygon points="85,175 115,175 108,215 92,215" fill="url(#shirtGrad)" />
          {/* Corporate Silk Tie */}
          <polygon points="97,175 103,175 106,230 100,240 94,230" fill="url(#tieGrad)" />
          {/* Suit Lapels */}
          <path d="M 65 185 L 90 225 L 82 240 L 45 240 Z" fill="#1E293B" opacity="0.9" />
          <path d="M 135 185 L 110 225 L 118 240 L 155 240 Z" fill="#1E293B" opacity="0.9" />

          {/* Neck */}
          <rect x="88" y="145" width="24" height="35" rx="4" fill="url(#skinGrad)" />
          {/* Neck Shadow */}
          <path d="M 88 152 Q 100 162 112 152 L 112 165 Q 100 172 88 165 Z" fill="#D4A373" opacity="0.4" />

          {/* Head & Face Contour */}
          <path
            d="M 68 75 C 68 35, 132 35, 132 75 C 132 115, 122 155, 100 155 C 78 155, 68 115, 68 75 Z"
            fill="url(#skinGrad)"
          />

          {/* Ears */}
          <ellipse cx="66" cy="88" rx="6" ry="12" fill="url(#skinGrad)" />
          <ellipse cx="134" cy="88" rx="6" ry="12" fill="url(#skinGrad)" />

          {/* Professional Groomed Hair */}
          <path
            d="M 64 70 C 64 25, 136 22, 136 70 C 134 50, 120 38, 100 38 C 76 38, 66 52, 64 70 Z"
            fill="url(#hairGrad)"
          />
          <path d="M 66 70 Q 72 45 100 45 Q 128 45 134 70 Q 120 52 100 52 Q 78 52 66 70 Z" fill="#334155" opacity="0.3" />

          {/* Eyebrows (reactive to speaking) */}
          <path
            d={state === 'speaking' ? 'M 78 68 Q 87 64 94 67' : 'M 78 70 Q 87 67 94 70'}
            stroke="#1F2937"
            strokeWidth="2.5"
            strokeLinecap="round"
            fill="none"
          />
          <path
            d={state === 'speaking' ? 'M 106 67 Q 113 64 122 68' : 'M 106 70 Q 113 67 122 70'}
            stroke="#1F2937"
            strokeWidth="2.5"
            strokeLinecap="round"
            fill="none"
          />

          {/* Eyes (Open vs Natural Blink) */}
          {isBlinking ? (
            <>
              {/* Closed Eyes line during blink */}
              <path d="M 78 82 Q 86 86 94 82" stroke="#374151" strokeWidth="2" strokeLinecap="round" fill="none" />
              <path d="M 106 82 Q 114 86 122 82" stroke="#374151" strokeWidth="2" strokeLinecap="round" fill="none" />
            </>
          ) : (
            <>
              {/* Left Eye */}
              <ellipse cx="86" cy="82" rx="7" ry="4.5" fill="#FFFFFF" />
              <circle cx="86" cy="82" r="3.2" fill="#1E3A8A" />
              <circle cx="86" cy="82" r="1.5" fill="#0F172A" />
              <circle cx="87.2" cy="80.8" r="0.9" fill="#FFFFFF" /> {/* Catchlight */}
              {/* Right Eye */}
              <ellipse cx="114" cy="82" rx="7" ry="4.5" fill="#FFFFFF" />
              <circle cx="114" cy="82" r="3.2" fill="#1E3A8A" />
              <circle cx="114" cy="82" r="1.5" fill="#0F172A" />
              <circle cx="115.2" cy="80.8" r="0.9" fill="#FFFFFF" /> {/* Catchlight */}
            </>
          )}

          {/* Nose */}
          <path d="M 100 82 L 98 106 L 104 106" stroke="#C99368" strokeWidth="1.6" strokeLinecap="round" fill="none" />

          {/* Articulated Mouth with Synchronized Lip Movements */}
          {mouthOpen && state === 'speaking' ? (
            mouthViseme === 1 ? (
              // Viseme 1: Slight open (consonants / short vowels)
              <g>
                <ellipse cx="100" cy="124" rx="9" ry="3.5" fill="#7F1D1D" />
                <path d="M 94 122.5 Q 100 124 106 122.5" stroke="#FFFFFF" strokeWidth="1.2" fill="none" />
                <path d="M 90 123 Q 100 121 110 123" stroke="#B91C1C" strokeWidth="1.5" fill="none" />
              </g>
            ) : mouthViseme === 2 ? (
              // Viseme 2: Wide open (ah, eh)
              <g>
                <ellipse cx="100" cy="125" rx="11" ry="6" fill="#6B1414" />
                <ellipse cx="100" cy="123" rx="8" ry="1.5" fill="#FFFFFF" /> {/* Top teeth */}
                <path d="M 90 122 Q 100 120 110 122" stroke="#B91C1C" strokeWidth="1.5" fill="none" />
                <path d="M 92 129 Q 100 132 108 129" stroke="#B91C1C" strokeWidth="1.5" fill="none" />
              </g>
            ) : mouthViseme === 3 ? (
              // Viseme 3: Round (oh, oo)
              <g>
                <ellipse cx="100" cy="124" rx="6" ry="6" fill="#6B1414" />
                <path d="M 94 121 Q 100 119 106 121" stroke="#B91C1C" strokeWidth="1.5" fill="none" />
              </g>
            ) : (
              // Viseme 4: Expressive speech
              <g>
                <ellipse cx="100" cy="124" rx="10" ry="4" fill="#7F1D1D" />
                <ellipse cx="100" cy="122.8" rx="7" ry="1.2" fill="#FFFFFF" />
              </g>
            )
          ) : (
            // Closed natural neutral smile (idle / listening)
            <path
              d="M 92 123 Q 100 127 108 123"
              stroke="#B45309"
              strokeWidth="2"
              strokeLinecap="round"
              fill="none"
            />
          )}
        </svg>

        {/* State Badge Overlay */}
        <div className="absolute top-2.5 left-2.5">
          <span
            className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold ${
              state === 'speaking'
                ? 'bg-blue-100 text-blue-800 border border-blue-300'
                : state === 'listening'
                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300 animate-pulse'
                : state === 'processing'
                ? 'bg-amber-100 text-amber-800 border border-amber-300'
                : 'bg-slate-100 text-slate-700 border border-slate-300'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                state === 'speaking'
                  ? 'bg-blue-600'
                  : state === 'listening'
                  ? 'bg-emerald-600'
                  : state === 'processing'
                  ? 'bg-amber-600'
                  : 'bg-slate-400'
              }`}
            />
            {statusText || (state === 'speaking' ? 'Interviewer Speaking' : state === 'listening' ? 'Listening to You' : state === 'processing' ? 'Evaluating Answer' : 'Interviewer Ready')}
          </span>
        </div>
      </div>

      {/* Subtitle / Question Live Captions Box */}
      {showCaptions && currentSpeechText && (
        <div className="w-full bg-slate-50 p-2.5 border-b border-slate-200 text-xs text-slate-700 max-h-20 overflow-y-auto leading-relaxed">
          <span className="font-semibold text-blue-900 block mb-0.5">Spoken Question:</span>
          "{currentSpeechText}"
        </div>
      )}

      {/* Interviewer Controls Footer */}
      <div className="w-full px-3 py-2 bg-white flex items-center justify-between text-xs text-slate-600">
        <div className="flex items-center gap-1.5">
          <button
            onClick={handleToggleMute}
            className={`p-1.5 rounded hover:bg-slate-100 transition-colors ${
              isMuted ? 'text-red-600 bg-red-50' : 'text-slate-600'
            }`}
            title={isMuted ? 'Unmute Interviewer' : 'Mute Interviewer'}
          >
            {isMuted ? <VolumeX size={15} /> : <Volume2 size={15} />}
          </button>
          <button
            onClick={handleReplay}
            className="p-1.5 rounded hover:bg-slate-100 text-slate-600 transition-colors"
            title="Replay Spoken Question"
          >
            <RotateCcw size={15} />
          </button>
          <button
            onClick={() => setShowCaptions(!showCaptions)}
            className={`p-1.5 rounded hover:bg-slate-100 transition-colors ${
              showCaptions ? 'text-blue-600 bg-blue-50' : 'text-slate-600'
            }`}
            title="Toggle Captions"
          >
            <MessageSquare size={15} />
          </button>
        </div>

        <span className="text-[11px] text-slate-500 font-medium">Virtual Human AI</span>
      </div>
    </div>
  );
};
