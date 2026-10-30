import React, { useEffect, useRef, useState } from 'react';
import { Shield, ShieldAlert, ShieldCheck, Eye, Users, AlertTriangle } from 'lucide-react';
import { integrityMonitor } from '../../services/integrityMonitor';
import { IntegrityWarning } from '../../types/integrity';

interface IntegrityPanelProps {
  stream: MediaStream | null;
  warningCount: number;
  onWarningTriggered: (warning: IntegrityWarning) => void;
}

export const IntegrityPanel: React.FC<IntegrityPanelProps> = ({
  stream,
  warningCount,
  onWarningTriggered,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [monitorStatus, setMonitorStatus] = useState({
    isMonitoring: false,
    lastCheckText: 'Initializing...',
    activeViolation: null as string | null,
  });

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
      videoRef.current.play().catch(() => {});
      integrityMonitor.startMonitoring(videoRef.current);
    }

    integrityMonitor.onStatusChange((status) => {
      setMonitorStatus(status);
    });

    integrityMonitor.onWarning((warning) => {
      onWarningTriggered(warning);
    });

    return () => {
      integrityMonitor.stopMonitoring();
    };
  }, [stream]);

  return (
    <div className="w-full bg-surface-container-low border border-outline-variant/30 rounded-xl p-3.5 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)]">
      <div className="flex items-center justify-between mb-2.5">
        <div className="flex items-center gap-1.5 font-mono text-secondary">
          <Shield size={16} />
          <span className="text-xs font-bold uppercase tracking-wider">
            Integrity Engine
          </span>
        </div>

        {/* Warning Indicator Chips */}
        <div className="flex items-center gap-1">
          <span
            className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full border ${
              warningCount === 0
                ? 'bg-secondary/15 text-secondary border-secondary/30'
                : warningCount === 1
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                : warningCount === 2
                ? 'bg-orange-500/20 text-orange-300 border-orange-500/40'
                : 'bg-error-container/40 text-error border-error/50'
            }`}
          >
            Warnings: {warningCount}/3
          </span>
        </div>
      </div>

      {/* Camera Viewport with Verification Bounding Box */}
      <div className="relative w-full h-36 bg-surface-container-lowest rounded-lg overflow-hidden mb-2.5 border border-outline-variant/30">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-cover"
        />

        {/* Live Centering Overlay Box */}
        <div className="absolute inset-4 border border-dashed border-secondary/30 rounded pointer-events-none flex items-center justify-center">
          <span className="text-[9px] font-mono text-secondary bg-surface-container-lowest/80 px-2 py-0.5 rounded border border-outline-variant/20">
            Authorized Focus Zone
          </span>
        </div>

        {/* Live Status Tag */}
        <div className="absolute bottom-2 left-2 flex items-center gap-1.5 bg-surface-container-lowest/90 border border-outline-variant/30 px-2 py-0.5 rounded text-[10px] font-mono text-on-surface">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              monitorStatus.activeViolation ? 'bg-amber-400 animate-ping' : 'bg-secondary'
            }`}
          />
          <span>{monitorStatus.activeViolation || 'Feed Verified'}</span>
        </div>
      </div>

      {/* Rules Active & Status Disclosure */}
      <div className="space-y-1.5 text-xs font-mono text-on-surface-variant">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1 text-[11px]">
            <Eye size={12} className="text-outline" /> Camera Feed Lock:
          </span>
          <span className="font-medium text-secondary text-[11px]">Enforced</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1 text-[11px]">
            <Users size={12} className="text-outline" /> Single Person View:
          </span>
          <span className="font-medium text-secondary text-[11px]">Active</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1 text-[11px]">
            <ShieldCheck size={12} className="text-outline" /> On-Device Processing:
          </span>
          <span className="font-medium text-primary text-[11px]">Private (Zero Uploads)</span>
        </div>
      </div>

      {/* Status Footer */}
      <div className="mt-2.5 pt-2 border-t border-outline-variant/20 flex items-center justify-between text-[10px] font-mono text-outline">
        <span>Status: {monitorStatus.lastCheckText}</span>
        <span>Grace: 3.0s Filter</span>
      </div>
    </div>
  );
};
