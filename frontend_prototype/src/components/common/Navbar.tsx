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
    <header className="sticky top-0 z-50 w-full px-6 py-3 flex items-center justify-between border-b border-outline-variant/30 bg-surface-container-lowest/90 backdrop-blur-xl shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)]">
      {/* Brand Cluster */}
      <div className="flex items-center space-x-6">
        <div
          className="flex items-center space-x-3 group cursor-pointer"
          onClick={() => onNavigate('home')}
        >
          <div className="h-8 w-8 rounded-lg bg-surface-container border border-outline-variant/40 flex items-center justify-center relative overflow-hidden group-hover:border-primary transition-colors">
            <div className="absolute inset-0 bg-primary/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <span className="material-symbols-outlined text-secondary" style={{ fontSize: '18px' }}>
              terminal
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="font-semibold tracking-tight text-on-surface text-base">
              IMAIRA FairScore
            </span>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono bg-surface-container-high border border-outline-variant/30 text-secondary">
              <span className="w-1.5 h-1.5 rounded-full bg-secondary mr-1 animate-pulse"></span>
              KERNEL v4.2
            </span>
          </div>
        </div>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center space-x-6 pl-4 border-l border-outline-variant/30 text-xs font-mono">
          <button
            onClick={() => onNavigate('home')}
            className={`transition-colors flex items-center gap-1.5 ${
              currentView === 'home'
                ? 'text-primary border-b-2 border-primary pb-0.5'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => onNavigate('setup')}
            className={`transition-colors flex items-center gap-1.5 ${
              currentView === 'setup' || currentView === 'interview'
                ? 'text-primary border-b-2 border-primary pb-0.5'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            <span>Live Room</span>
            {currentView === 'interview' && (
              <span className="px-1.5 py-0.2 bg-secondary/10 text-secondary text-[9px] rounded font-mono">
                Active
              </span>
            )}
          </button>
          <button
            onClick={() => onNavigate('evaluation')}
            className={`transition-colors flex items-center gap-1.5 ${
              currentView === 'evaluation'
                ? 'text-primary border-b-2 border-primary pb-0.5'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            <span>Evaluations</span>
            {currentView === 'evaluation' && (
              <span className="px-1.5 py-0.2 bg-primary/10 text-primary text-[9px] rounded font-mono">
                Dossier
              </span>
            )}
          </button>
          <button
            onClick={() => onNavigate('judge')}
            className={`transition-colors flex items-center gap-1.5 ${
              currentView === 'judge'
                ? 'text-primary border-b-2 border-primary pb-0.5'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            <span>⚖️ Judge Console</span>
          </button>
          <a
            href="https://github.com/Krishna-neural/IMAIRA-Fairscore.git"
            target="_blank"
            rel="noopener noreferrer"
            className="text-on-surface-variant hover:text-on-surface transition-colors flex items-center gap-1"
          >
            <span>GitHub</span>
            <span className="text-[10px]">↗</span>
          </a>
        </nav>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-3">
        {/* Backend Online Telemetry Badge */}
        <div className="hidden lg:flex items-center space-x-2 px-2.5 py-1 rounded bg-surface-container-low border border-outline-variant/20 text-xs font-mono text-on-surface-variant">
          <span
            className={`w-2 h-2 rounded-full ${
              health ? 'bg-secondary animate-pulse' : 'bg-error'
            }`}
          />
          <span>
            {health
              ? `Port ${health.port || 8002} Online • ${health.glossary_terms_loaded} Terms`
              : 'Connecting...'}
          </span>
        </div>

        {/* Start Interview CTA */}
        <button
          onClick={() => onNavigate('setup')}
          disabled={isRestricted}
          className="relative inline-flex items-center px-4 py-1.5 rounded-lg bg-primary-container text-on-primary-container text-xs font-medium shadow-[0_0_20px_rgba(108,136,255,0.4)] hover:bg-primary-fixed-dim transition-all active:scale-[0.98] disabled:opacity-50"
        >
          <span className="material-symbols-outlined mr-1.5 text-on-primary-container" style={{ fontSize: '16px' }}>
            play_arrow
          </span>
          <span>{isRestricted ? 'Restricted' : 'Start Interview'}</span>
        </button>
      </div>
    </header>
  );
};
