import React, { useState } from 'react';
import { Mic, MicOff, Video, VideoOff, LogOut, CheckCircle2 } from 'lucide-react';

interface ControlBarProps {
  isMicMuted: boolean;
  isCameraOn: boolean;
  onToggleMic: () => void;
  onToggleCamera: () => void;
  onEndInterview: () => void;
}

export const ControlBar: React.FC<ControlBarProps> = ({
  isMicMuted,
  isCameraOn,
  onToggleMic,
  onToggleCamera,
  onEndInterview,
}) => {
  const [showConfirmEnd, setShowConfirmEnd] = useState(false);

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-xs flex items-center justify-between font-sans flex-wrap gap-2">
      <div className="flex items-center gap-2">
        <button
          onClick={onToggleMic}
          className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-bold border transition-all ${
            isMicMuted
              ? 'bg-red-50 text-red-700 border-red-200 hover:bg-red-100'
              : 'bg-slate-50 text-slate-700 border-slate-300 hover:bg-slate-100'
          }`}
        >
          {isMicMuted ? <MicOff size={15} /> : <Mic size={15} />}
          <span>{isMicMuted ? 'Unmute Mic' : 'Mute Mic'}</span>
        </button>

        <button
          onClick={onToggleCamera}
          className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-bold border transition-all ${
            !isCameraOn
              ? 'bg-slate-100 text-slate-500 border-slate-300 hover:bg-slate-200'
              : 'bg-emerald-50 text-emerald-800 border-emerald-300'
          }`}
        >
          {!isCameraOn ? <VideoOff size={15} /> : <Video size={15} />}
          <span>{isCameraOn ? 'Camera On' : 'Camera Off'}</span>
        </button>
      </div>

      <div className="flex items-center gap-2">
        {showConfirmEnd ? (
          <div className="flex items-center gap-2 animate-fadeIn">
            <span className="text-xs text-slate-600 font-semibold">Finish interview now?</span>
            <button
              onClick={() => {
                setShowConfirmEnd(false);
                onEndInterview();
              }}
              className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-bold shadow-xs transition-colors"
            >
              Yes, Generate Scorecard
            </button>
            <button
              onClick={() => setShowConfirmEnd(false)}
              className="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors"
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            onClick={() => setShowConfirmEnd(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold bg-[#101C35] hover:bg-[#1b2b4d] text-white transition-all shadow-xs"
          >
            <LogOut size={14} />
            <span>Finish & View Scorecard</span>
          </button>
        )}
      </div>
    </div>
  );
};
