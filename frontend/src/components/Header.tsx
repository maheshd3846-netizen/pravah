import React from 'react';

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
  const tabs: { id: NavTab; label: string }[] = [
    { id: 'COMMAND_CENTER', label: 'COMMAND CENTER' },
    { id: 'NETWORK', label: 'NETWORK' },
    { id: 'FORECAST', label: 'FORECAST' },
    { id: 'RISK', label: 'RISK' },
    { id: 'OPTIMIZATION', label: 'OPTIMIZATION' },
    { id: 'SIMULATION', label: 'SIMULATION' },
    { id: 'RECOMMENDATIONS', label: 'RECOMMENDATIONS' },
    { id: 'AUDIT', label: 'AUDIT / EVIDENCE' },
  ];

  return (
    <header className="header" role="banner">
      {/* Left: Brand / Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '4px',
            background: 'linear-gradient(135deg, #1d4ed8, #06b6d4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 800,
            fontSize: '14px',
            color: '#fff',
            letterSpacing: '0.05em',
          }}
        >
          P
        </div>
        <div>
          <div style={{ fontSize: '13px', fontWeight: 800, letterSpacing: '0.08em', color: '#f8fafc' }}>
            PRAVAH
          </div>
          <div style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#64748b' }}>
            Predictive Logistics Intelligence
          </div>
        </div>
      </div>

      {/* Center: Main Navigation */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: '4px' }} aria-label="Main Navigation">
        {tabs.map((tab) => {
          const isActive = currentTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              style={{
                background: isActive ? '#1e293b' : 'transparent',
                color: isActive ? '#38bdf8' : '#94a3b8',
                border: 'none',
                borderBottom: isActive ? '2px solid #38bdf8' : '2px solid transparent',
                padding: '6px 10px',
                fontSize: '11px',
                fontWeight: 600,
                letterSpacing: '0.04em',
                cursor: 'pointer',
                borderRadius: '2px 2px 0 0',
                transition: 'all 0.15s ease',
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </nav>

      {/* Right: Actions, Demo Mode & System Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <button
          onClick={onAnalyzeClick}
          disabled={isAnalyzing}
          className="btn btn-primary"
          style={{ padding: '4px 10px', fontSize: '10px' }}
        >
          {isAnalyzing ? 'ANALYZING...' : '⚡ ANALYZE NETWORK'}
        </button>

        <button
          onClick={onToggleDemoMode}
          className="btn btn-secondary"
          style={{
            padding: '4px 10px',
            fontSize: '10px',
            borderColor: demoMode ? '#06b6d4' : undefined,
            color: demoMode ? '#06b6d4' : undefined,
          }}
        >
          {demoMode ? 'DEMO ACTIVE ★' : 'DEMO MODE'}
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
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
            letterSpacing: '0.04em',
          }}
        >
          Synthetic Simulation
        </div>
      </div>
    </header>
  );
};
