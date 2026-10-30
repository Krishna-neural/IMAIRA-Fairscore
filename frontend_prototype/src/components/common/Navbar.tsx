import React, { useEffect, useState } from 'react';
import { apiService } from '../../services/apiService';
import { HealthResponse } from '../../types/api';

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
    <header className="sticky top-0 z-40 bg-white border-b border-slate-200 shadow-xs px-6 py-3 flex items-center justify-between">
      {/* Brand */}
      <div
        className="flex items-center gap-3 cursor-pointer select-none"
        onClick={() => onNavigate('home')}
      >
        <div className="w-9 h-9 rounded bg-[#101C35] flex items-center justify-center text-white font-extrabold text-sm border border-[#172846]">
          IF
        </div>
        <div>
          <span className="text-base font-extrabold text-[#101C35] tracking-tight block leading-tight">
            IMAIRA FairScore
          </span>
          <span className="text-[11px] text-slate-500 font-medium block">
            Evaluate Knowledge. Not Accents.
          </span>
        </div>
      </div>

      {/* Nav Links */}
      <nav className="hidden md:flex items-center gap-1 text-sm font-medium">
        <button
          onClick={() => onNavigate('home')}
          className={`px-3 py-1.5 rounded transition-colors ${
            currentView === 'home'
              ? 'text-blue-700 bg-blue-50 font-semibold'
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
          className="px-3 py-1.5 rounded text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors"
        >
          How It Works
        </button>
        <button
          onClick={() => onNavigate('setup')}
          className={`px-3 py-1.5 rounded transition-colors ${
            currentView === 'setup' || currentView === 'interview'
              ? 'text-blue-700 bg-blue-50 font-semibold'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          Start Interview
        </button>
        <button
          onClick={() => onNavigate('evaluation')}
          className={`px-3 py-1.5 rounded transition-colors ${
            currentView === 'evaluation'
              ? 'text-blue-700 bg-blue-50 font-semibold'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          Evaluation
        </button>
        <button
          onClick={() => onNavigate('judge')}
          className={`px-3 py-1.5 rounded transition-colors ${
            currentView === 'judge'
              ? 'text-blue-700 bg-blue-50 font-semibold'
              : 'text-slate-700 bg-slate-100 hover:bg-slate-200'
          }`}
        >
          ⚖️ Judge Console
        </button>
        <a
          href="https://github.com/Krishna-neural/IMAIRA-Fairscore.git"
          target="_blank"
          rel="noopener noreferrer"
          className="px-3 py-1.5 rounded text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors"
        >
          GitHub ↗
        </a>
      </nav>

      {/* Right Actions */}
      <div className="flex items-center gap-3">
        {/* Backend Status Pill */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-50 border border-slate-200 rounded-full text-xs text-slate-600">
          <span
            className={`w-2 h-2 rounded-full ${
              health ? 'bg-emerald-600' : 'bg-red-500'
            }`}
          />
          <span>
            {health
              ? `Port ${health.port || 8002} Online • ${health.glossary_terms_loaded} Terms`
              : 'Connecting...'}
          </span>
        </div>

        {/* CTA Button */}
        <button
          onClick={() => onNavigate('setup')}
          disabled={isRestricted}
          className="hidden sm:inline-flex items-center justify-center px-4 py-1.5 bg-[#2457A6] hover:bg-[#1A4482] text-white rounded text-xs font-semibold shadow-xs transition-colors disabled:opacity-50"
        >
          {isRestricted ? 'Restricted' : 'Start Interview'}
        </button>
      </div>
    </header>
  );
};
