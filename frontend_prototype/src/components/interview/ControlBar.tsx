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
    <div className="bg-surface-container-low border border-outline-variant/30 rounded-xl p-3 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)] flex items-center justify-between">
      <div className="flex items-center gap-2">
        <button
          onClick={onToggleMic}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-semibold border transition-all ${
            isMicMuted
              ? 'bg-error-container/20 text-error border-error/30 hover:bg-error-container/40'
              : 'bg-surface-container text-on-surface border-outline-variant/30 hover:bg-surface-container-high'
          }`}
        >
          {isMicMuted ? <MicOff size={14} /> : <Mic size={14} />}
          <span>{isMicMuted ? 'Unmute Mic' : 'Mute Mic'}</span>
        </button>

        <button
          onClick={onToggleCamera}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-semibold border transition-all ${
            !isCameraOn
              ? 'bg-error-container/20 text-error border-error/30 hover:bg-error-container/40'
              : 'bg-surface-container text-on-surface border-outline-variant/30 hover:bg-surface-container-high'
          }`}
        >
          {!isCameraOn ? <VideoOff size={14} /> : <Video size={14} />}
          <span>{isCameraOn ? 'Camera Active' : 'Camera Off'}</span>
        </button>
      </div>

      <button
        onClick={onEndInterview}
        className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-mono font-semibold bg-error-container/20 hover:bg-error-container/40 border border-error/30 text-error transition-all duration-150 active:scale-[0.98]"
      >
        <LogOut size={14} />
        <span>Conclude & Generate Scorecard</span>
      </button>
    </div>
  );
};
