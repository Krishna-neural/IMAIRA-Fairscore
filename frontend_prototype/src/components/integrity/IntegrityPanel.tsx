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
    <div className="w-full bg-white border border-slate-200 rounded-lg p-3 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          <Shield className="text-blue-700" size={16} />
          <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Integrity Monitor
          </span>
        </div>

        {/* Warning Indicator Chips */}
        <div className="flex items-center gap-1">
          <span
            className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
              warningCount === 0
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : warningCount === 1
                ? 'bg-amber-50 text-amber-700 border border-amber-200'
                : warningCount === 2
                ? 'bg-orange-50 text-orange-700 border border-orange-200'
                : 'bg-red-50 text-red-700 border border-red-200'
            }`}
          >
            Warnings: {warningCount}/3
          </span>
        </div>
      </div>

      {/* Camera Viewport with Verification Bounding Box */}
      <div className="relative w-full h-36 bg-slate-900 rounded overflow-hidden mb-2 border border-slate-300">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-cover"
        />

        {/* Live Centering Overlay Box */}
        <div className="absolute inset-4 border border-dashed border-white/40 rounded pointer-events-none flex items-center justify-center">
          <span className="text-[10px] text-white/60 bg-black/40 px-1.5 py-0.5 rounded">
            Authorized Zone
          </span>
        </div>

        {/* Live Status Tag */}
        <div className="absolute bottom-2 left-2 flex items-center gap-1 bg-black/75 px-1.5 py-0.5 rounded text-[10px] text-white">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              monitorStatus.activeViolation ? 'bg-amber-400 animate-ping' : 'bg-emerald-400'
            }`}
          />
          <span>{monitorStatus.activeViolation || 'Feed Verified'}</span>
        </div>
      </div>

      {/* Rules Active & Status Disclosure */}
      <div className="space-y-1 text-[11px] text-slate-600">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1">
            <Eye size={12} className="text-slate-400" /> Camera Feed Lock:
          </span>
          <span className="font-medium text-emerald-700">Enforced</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1">
            <Users size={12} className="text-slate-400" /> Single Person View:
          </span>
          <span className="font-medium text-emerald-700">Active</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1">
            <ShieldCheck size={12} className="text-slate-400" /> On-Device Processing:
          </span>
          <span className="font-medium text-blue-700">Private (Zero Uploads)</span>
        </div>
      </div>

      {/* Status Footer */}
      <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-500">
        <span>Status: {monitorStatus.lastCheckText}</span>
        <span>Grace: 3.0s Filter</span>
      </div>
    </div>
  );
};
