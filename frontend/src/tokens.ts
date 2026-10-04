/**
 * PRAVAH Spatial Decision Intelligence Platform Tokens
 * Dark navy foundation, restrained teal accent, semantic amber/red/green
 */

export const tokens = {
  colors: {
    background: {
      app: 'var(--bg-app, #08111F)',
      surface: 'var(--bg-surface, #0D1828)',
      secondary: 'var(--bg-secondary, #111F31)',
      elevated: 'var(--bg-elevated, #111F31)',
      hover: 'var(--bg-hover, #16263A)',
      drawer: 'var(--bg-drawer, #0D1828)',
    },
    border: {
      default: 'var(--border-default, rgba(255, 255, 255, 0.08))',
      subtle: 'var(--border-subtle, rgba(255, 255, 255, 0.05))',
      hover: 'var(--border-hover, rgba(255, 255, 255, 0.14))',
      focus: 'var(--border-focus, #31B89A)',
    },
    text: {
      primary: 'var(--text-primary, #F3F6FA)',
      secondary: 'var(--text-secondary, #A7B4C5)',
      muted: 'var(--text-muted, #6F8095)',
    },
    brand: {
      primary: 'var(--brand-primary, #31B89A)',
      primaryHover: 'var(--brand-primary-hover, #42C9AA)',
      primarySoft: 'var(--brand-soft, rgba(49, 184, 154, 0.12))',
      primaryBorder: 'var(--brand-border, rgba(49, 184, 154, 0.28))',
    },
    status: {
      healthy: 'var(--status-healthy, #35C98A)',
      healthySoft: 'var(--status-healthy-soft, rgba(53, 201, 138, 0.12))',
      healthyBorder: 'var(--status-healthy-border, rgba(53, 201, 138, 0.25))',

      warning: 'var(--status-warning, #E8B44F)',
      warningSoft: 'var(--status-warning-soft, rgba(232, 180, 79, 0.12))',
      warningBorder: 'var(--status-warning-border, rgba(232, 180, 79, 0.25))',

      highRisk: 'var(--status-highrisk, #F47C55)',
      highRiskSoft: 'var(--status-highrisk-soft, rgba(244, 124, 85, 0.12))',
      highRiskBorder: 'var(--status-highrisk-border, rgba(244, 124, 85, 0.25))',

      critical: 'var(--status-critical, #E55353)',
      criticalSoft: 'var(--status-critical-soft, rgba(229, 83, 83, 0.12))',
      criticalBorder: 'var(--status-critical-border, rgba(229, 83, 83, 0.25))',

      info: 'var(--status-info, #69A9F8)',
      infoSoft: 'var(--status-info-soft, rgba(105, 169, 248, 0.12))',
      infoBorder: 'var(--status-info-border, rgba(105, 169, 248, 0.25))',
    },
  },
  radii: {
    container: '8px',
    panel: '8px',
    card: '6px',
    button: '6px',
    input: '6px',
    badge: '5px',
  },
  typography: {
    fontSans: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    fontMono: "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace",
  },
  shadows: {
    subtle: 'var(--shadow-subtle, 0 4px 20px rgba(0, 0, 0, 0.25))',
    drawer: 'var(--shadow-drawer, -6px 0 24px rgba(0, 0, 0, 0.4))',
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
    xxl: '32px',
  },
} as const;

export type DesignTokens = typeof tokens;
