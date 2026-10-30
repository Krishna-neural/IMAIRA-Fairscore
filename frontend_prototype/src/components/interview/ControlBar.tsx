import React from 'react';
import { Mic, MicOff, Video, VideoOff, LogOut } from 'lucide-react';

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
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-2.5 shadow-xs flex items-center justify-between">
      <div className="flex items-center gap-2">
        <button
          onClick={onToggleMic}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold border transition-colors ${
            isMicMuted
              ? 'bg-red-50 text-red-700 border-red-200 hover:bg-red-100'
              : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
          }`}
        >
          {isMicMuted ? <MicOff size={14} /> : <Mic size={14} />}
          <span>{isMicMuted ? 'Unmute Mic' : 'Mute Mic'}</span>
        </button>

        <button
          onClick={onToggleCamera}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold border transition-colors ${
            !isCameraOn
              ? 'bg-red-50 text-red-700 border-red-200 hover:bg-red-100'
              : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
          }`}
        >
          {!isCameraOn ? <VideoOff size={14} /> : <Video size={14} />}
          <span>{isCameraOn ? 'Camera Active' : 'Camera Off'}</span>
        </button>
      </div>

      <button
        onClick={onEndInterview}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold bg-red-600 hover:bg-red-700 text-white transition-colors shadow-xs"
      >
        <LogOut size={14} />
        <span>Conclude & Evaluate</span>
      </button>
    </div>
  );
};
