import React, { useEffect, useState } from 'react';
import { apiService } from '../../services/apiService';
import { HealthResponse } from '../../types/api';
import { GraduationCap, ShieldCheck, Scale, Globe } from 'lucide-react';

interface NavbarProps {
  currentView: string;
  onNavigate: (view: string) => void;
  isRestricted?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ currentView, onNavigate, isRestricted }) => {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    const poll = async () => {
      try {
        const data = await apiService.checkHealth();
        setHealth(data);
      } catch (_) {
        setHealth(null);
      }
    };
    poll();
    const interval = setInterval(poll, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-xs px-4 sm:px-6 py-3 flex items-center justify-between font-sans">
      {/* Brand */}
      <div
        className="flex items-center gap-3 cursor-pointer select-none"
        onClick={() => onNavigate('home')}
      >
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#101C35] to-[#2457A6] flex items-center justify-center text-white font-black text-sm shadow-xs border border-blue-900">
          IF
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-base font-black text-[#101C35] tracking-tight leading-tight">
              IMAIRA FairScore
            </span>
            <span className="hidden sm:inline-block px-2 py-0.2 rounded-full text-[10px] font-extrabold bg-blue-50 text-[#1A4482] border border-blue-200">
              AI FRONTIER
            </span>
          </div>
          <span className="text-[11px] text-slate-500 font-medium block leading-tight">
            Hear the answer, not the accent.
          </span>
        </div>
      </div>

      {/* Nav Links */}
      <nav className="hidden md:flex items-center gap-1 text-xs font-bold">
        <button
          onClick={() => onNavigate('home')}
          className={`px-3 py-1.5 rounded-lg transition-all ${
            currentView === 'home'
              ? 'text-[#2457A6] bg-blue-50/80 shadow-xs font-black'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => {
            onNavigate('home');
            setTimeout(() => {
              document.getElementById('howItWorksSection')?.scrollIntoView({ behavior: 'smooth' });
            }, 100);
          }}
          className="px-3 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-all"
        >
          How It Works
        </button>
        <button
          onClick={() => onNavigate('setup')}
          className={`px-3 py-1.5 rounded-lg transition-all ${
            currentView === 'setup' || currentView === 'interview'
              ? 'text-[#2457A6] bg-blue-50/80 shadow-xs font-black'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          Practice Interview
        </button>
        <button
          onClick={() => onNavigate('evaluation')}
          className={`px-3 py-1.5 rounded-lg transition-all ${
            currentView === 'evaluation'
              ? 'text-[#2457A6] bg-blue-50/80 shadow-xs font-black'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          Scorecard & Coaching
        </button>
        <button
          onClick={() => onNavigate('judge')}
          className={`px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-1 ${
            currentView === 'judge'
              ? 'text-[#2457A6] bg-blue-50/80 shadow-xs font-black'
              : 'text-slate-700 bg-slate-100 hover:bg-slate-200'
          }`}
        >
          <Scale size={13} className="text-[#2457A6]" />
          <span>Placement & Judge Console</span>
        </button>
      </nav>

      {/* Right Actions */}
      <div className="flex items-center gap-2.5">
        {/* Backend & Glossary Status Pill */}
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 bg-slate-50 border border-slate-200 rounded-full text-xs text-slate-600">
          <span
            className={`w-2 h-2 rounded-full ${
              health ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'
            }`}
          />
          <span className="font-medium text-[11px]">
            {health
              ? `Port ${health.port || 8002} • ${health.glossary_terms_loaded} Terms Active`
              : 'Connecting...'}
          </span>
        </div>

        {/* CTA Button */}
        <button
          onClick={() => onNavigate('setup')}
          disabled={isRestricted}
          className="inline-flex items-center justify-center gap-1.5 px-4 py-2 bg-[#2457A6] hover:bg-[#1A4482] text-white rounded-lg text-xs font-bold shadow-xs hover:shadow transition-all disabled:opacity-50"
        >
          <GraduationCap size={15} />
          <span>{isRestricted ? 'Restricted' : 'Start Practice'}</span>
        </button>
      </div>
    </header>
  );
};
