import React, { useState, useEffect } from 'react';

export type NavTab =
  | 'COMMAND_CENTER'
  | 'NETWORK'
  | 'FORECAST'
  | 'RISK'
  | 'OPTIMIZATION'
  | 'SIMULATION'
  | 'RECOMMENDATIONS'
  | 'AUDIT';

interface HeaderProps {
  currentTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  onAnalyzeClick: () => void;
  isAnalyzing: boolean;
  demoMode: boolean;
  onToggleDemoMode: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  onTabChange,
  onAnalyzeClick,
  isAnalyzing,
  demoMode,
  onToggleDemoMode,
}) => {
  const [zuluTime, setZuluTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const hours = String(now.getUTCHours()).padStart(2, '0');
      const minutes = String(now.getUTCMinutes()).padStart(2, '0');
      const seconds = String(now.getUTCSeconds()).padStart(2, '0');
      setZuluTime(`${hours}:${minutes}:${seconds}Z`);
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const tabs: { id: NavTab; label: string; icon: string }[] = [
    { id: 'COMMAND_CENTER', label: 'COMMAND CENTER', icon: '◈' },
    { id: 'NETWORK', label: 'NETWORK', icon: '☵' },
    { id: 'FORECAST', label: 'FORECAST', icon: '∿' },
    { id: 'RISK', label: 'RISK', icon: '⚠' },
    { id: 'OPTIMIZATION', label: 'OPTIMIZATION', icon: '⚡' },
    { id: 'SIMULATION', label: 'SIMULATION', icon: '◬' },
    { id: 'RECOMMENDATIONS', label: 'RECOMMENDATIONS', icon: '◎' },
    { id: 'AUDIT', label: 'AUDIT / EVIDENCE', icon: '☶' },
  ];

  return (
    <header className="header" role="banner">
      {/* Left: Brand / Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '6px',
            background: 'linear-gradient(135deg, #1e3a8a 0%, #0284c7 50%, #06b6d4 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 12px rgba(6, 182, 212, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.4)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.2">
            <polygon points="12 2 19 8.5 19 15.5 12 22 5 15.5 5 8.5" />
            <line x1="12" y1="2" x2="12" y2="22" strokeDasharray="2 2" strokeWidth="1.5" />
            <circle cx="12" cy="12" r="3" fill="#ffffff" />
          </svg>
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: '16px',
                fontWeight: 800,
                letterSpacing: '0.12em',
                color: '#f8fafc',
                textShadow: '0 0 12px rgba(56, 189, 248, 0.4)',
              }}
            >
              PRAVAH
            </span>
            <span
              style={{
                fontSize: '9px',
                padding: '1px 5px',
                borderRadius: '2px',
                background: 'rgba(0, 229, 255, 0.12)',
                color: 'var(--accent-cyan)',
                border: '1px solid rgba(0, 229, 255, 0.3)',
                fontFamily: 'var(--font-mono)',
                fontWeight: 600,
              }}
            >
              DEFENSE C2
            </span>
          </div>
          <div
            style={{
              fontSize: '9px',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-sans)',
            }}
          >
            Predictive Logistics Intelligence & Resilience Engine
          </div>
        </div>
      </div>

      {/* Center: Main Navigation */}
      <nav
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '3px',
          background: 'rgba(10, 16, 28, 0.6)',
          padding: '3px',
          borderRadius: '6px',
          border: '1px solid var(--border-subtle)',
        }}
        aria-label="Main Navigation"
      >
        {tabs.map((tab) => {
          const isActive = currentTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              style={{
                background: isActive
                  ? 'linear-gradient(180deg, rgba(30, 45, 71, 0.85) 0%, rgba(18, 27, 44, 0.85) 100%)'
                  : 'transparent',
                color: isActive ? '#38bdf8' : '#94a3b8',
                border: isActive
                  ? '1px solid rgba(56, 189, 248, 0.4)'
                  : '1px solid transparent',
                borderBottom: isActive ? '2px solid #38bdf8' : '2px solid transparent',
                padding: '5px 11px',
                fontSize: '11px',
                fontWeight: 600,
                letterSpacing: '0.04em',
                cursor: 'pointer',
                borderRadius: '4px',
                transition: 'all 0.15s cubic-bezier(0.16, 1, 0.3, 1)',
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                boxShadow: isActive ? '0 2px 8px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.1)' : 'none',
              }}
            >
              <span style={{ fontSize: '10px', opacity: isActive ? 1 : 0.6 }}>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Right: Actions, Demo Mode & System Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {/* Zulu Time Display */}
        {zuluTime && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(15, 23, 42, 0.6)',
              padding: '3px 8px',
              borderRadius: '4px',
              border: '1px solid var(--border-subtle)',
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              color: '#cbd5e1',
            }}
          >
            <span style={{ color: '#06b6d4', fontSize: '9px' }}>⏱</span>
            <span>{zuluTime}</span>
          </div>
        )}

        <button
          onClick={onAnalyzeClick}
          disabled={isAnalyzing}
          className="btn btn-primary"
          style={{ padding: '4px 12px', fontSize: '10px' }}
        >
          {isAnalyzing ? 'ANALYZING...' : '⚡ ANALYZE NETWORK'}
        </button>

        <button
          onClick={onToggleDemoMode}
          className="btn btn-secondary"
          style={{
            padding: '4px 11px',
            fontSize: '10px',
            borderColor: demoMode ? 'rgba(0, 229, 255, 0.6)' : undefined,
            color: demoMode ? '#00e5ff' : undefined,
            background: demoMode ? 'rgba(0, 229, 255, 0.12)' : undefined,
          }}
        >
          {demoMode ? 'DEMO ACTIVE ★' : 'DEMO MODE'}
        </button>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(16, 185, 129, 0.08)',
            border: '1px solid rgba(16, 185, 129, 0.25)',
            padding: '3px 8px',
            borderRadius: '4px',
          }}
        >
          <span className="pulse-indicator" style={{ backgroundColor: '#10b981' }} />
          <span style={{ fontSize: '10px', fontWeight: 600, color: '#10b981', letterSpacing: '0.04em' }}>
            SYSTEM READY
          </span>
        </div>

        <div
          style={{
            borderLeft: '1px solid rgba(255, 255, 255, 0.1)',
            paddingLeft: '10px',
            fontSize: '10px',
            color: '#64748b',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            fontFamily: 'var(--font-mono)',
          }}
        >
          Synthetic Simulation
        </div>
      </div>
    </header>
  );
};
