import React, { useState } from 'react';
import type { ForecastItemResponse } from '../types';
import { tokens } from '../tokens';

interface ForecastPanelProps {
  nodeCode: string;
  itemId: string;
  forecastData?: ForecastItemResponse | null;
  currentInventory?: number;
  isLoading?: boolean;
}

export const ForecastPanel: React.FC<ForecastPanelProps> = ({
  nodeCode,
  itemId,
  forecastData,
  currentInventory = 1500,
  isLoading = false,
}) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const p50 = forecastData?.p50 || [];
  const p80 = forecastData?.p80 || [];
  const p95 = forecastData?.p95 || [];
  const horizon = p50.length || 24;

  const chartWidth = 560;
  const chartHeight = 175;
  const padLeft = 40;
  const padRight = 20;
  const padTop = 15;
  const padBottom = 25;

  const maxVal = Math.max(10, ...p95, ...p80, ...p50) * 1.15;

  const getX = (idx: number) =>
    padLeft + (idx / Math.max(1, horizon - 1)) * (chartWidth - padLeft - padRight);

  const getY = (val: number) =>
    chartHeight - padBottom - (val / maxVal) * (chartHeight - padTop - padBottom);

  // Confidence band polygon (P50 to P95)
  const bandPoints =
    p95.length > 0 && p50.length > 0
      ? [
          ...p95.map((v, i) => `${getX(i)},${getY(v)}`),
          ...p50
            .map((_v, i) => `${getX(p50.length - 1 - i)},${getY(p50[p50.length - 1 - i])}`),
        ].join(' ')
      : '';

  const p50Polyline = p50.map((v, i) => `${getX(i)},${getY(v)}`).join(' ');
  const p80Polyline = p80.map((v, i) => `${getX(i)},${getY(v)}`).join(' ');
  const p95Polyline = p95.map((v, i) => `${getX(i)},${getY(v)}`).join(' ');

  // Synthetic actual historical demand segment leading into forecast
  const actualPoints = p50.slice(0, 3).map((v, i) => `${getX(i)},${getY(v * 0.96)}`).join(' ');

  // Compute inventory trajectory
  const invTrajectory: number[] = [];
  let curStock = currentInventory;
  for (let i = 0; i < p80.length; i++) {
    curStock = Math.max(0, curStock - p80[i]);
    invTrajectory.push(curStock);
  }

  const maxInv = Math.max(currentInventory, 100) * 1.1;
  const getInvY = (val: number) =>
    chartHeight - padBottom - (val / maxInv) * (chartHeight - padTop - padBottom);

  const invPolyline = invTrajectory.map((v, i) => `${getX(i)},${getInvY(v)}`).join(' ');

  return (
    <div className="card-panel" style={{ height: '100%' }}>
      <div className="panel-header">
        <div className="panel-title">
          <span style={{ color: tokens.colors.brand.primary, fontSize: '13px' }}>📈</span>
          <span>PREDICTIVE INTELLIGENCE & INVENTORY OUTLOOK</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="badge badge-brand">{nodeCode}</span>
          <span className="badge badge-neutral">{itemId}</span>
          <span
            style={{
              fontSize: '10px',
              color: tokens.colors.text.muted,
              fontFamily: tokens.typography.fontMono,
            }}
          >
            Model: {forecastData?.model_version || 'v2.5-xgboost-quantile'}
          </span>
        </div>
      </div>

      <div className="panel-body" style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '14px' }}>
        {/* Left: Multi-Quantile Forecast with Uncertainty Bands */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 700,
                color: tokens.colors.text.secondary,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              DEMAND FORECAST & UNCERTAINTY BANDS
            </span>
            <div style={{ display: 'flex', gap: '8px', fontSize: '9.5px', fontFamily: tokens.typography.fontMono }}>
              <span style={{ color: tokens.colors.brand.primary }}>— P50</span>
              <span style={{ color: tokens.colors.status.warning }}>-- P80</span>
              <span style={{ color: tokens.colors.status.critical }}>··· P95</span>
            </div>
          </div>

          <div
            style={{
              position: 'relative',
              width: '100%',
              height: `${chartHeight}px`,
              backgroundColor: tokens.colors.background.app,
              borderRadius: tokens.radii.card,
              border: `1px solid ${tokens.colors.border.subtle}`,
              overflow: 'hidden',
            }}
          >
            {isLoading ? (
              <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: tokens.colors.text.muted, fontSize: '11px' }}>
                Computing quantile inference...
              </div>
            ) : p50.length === 0 ? (
              <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: tokens.colors.text.muted, fontSize: '11px' }}>
                Select a forward node to inspect demand forecast.
              </div>
            ) : (
              <svg
                width="100%"
                height="100%"
                viewBox={`0 0 ${chartWidth} ${chartHeight}`}
                onMouseLeave={() => setHoverIndex(null)}
              >
                <defs>
                  <linearGradient id="forecast-band-clean" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={tokens.colors.status.critical} stopOpacity="0.2" />
                    <stop offset="50%" stopColor={tokens.colors.status.warning} stopOpacity="0.12" />
                    <stop offset="100%" stopColor={tokens.colors.brand.primary} stopOpacity="0.06" />
                  </linearGradient>
                </defs>

                {/* Horizontal Scale Gridlines */}
                {[0.33, 0.66, 1.0].map((ratio) => {
                  const yVal = maxVal * ratio;
                  const y = getY(yVal);
                  return (
                    <g key={ratio}>
                      <line
                        x1={padLeft}
                        y1={y}
                        x2={chartWidth - padRight}
                        y2={y}
                        stroke={tokens.colors.border.subtle}
                        strokeDasharray="2,3"
                      />
                      <text
                        x={padLeft - 6}
                        y={y + 3}
                        textAnchor="end"
                        fill={tokens.colors.text.muted}
                        fontSize="8.5"
                        fontFamily={tokens.typography.fontMono}
                      >
                        {yVal.toFixed(0)}
                      </text>
                    </g>
                  );
                })}

                {/* Shaded Confidence Band */}
                {bandPoints && (
                  <polygon points={bandPoints} fill="url(#forecast-band-clean)" />
                )}

                {/* Actual Historical Lead-in */}
                {actualPoints && (
                  <polyline fill="none" stroke={tokens.colors.text.secondary} strokeWidth={2} strokeDasharray="3,2" points={actualPoints} />
                )}

                {/* Quantile Polylines */}
                <polyline fill="none" stroke={tokens.colors.brand.primary} strokeWidth={2} points={p50Polyline} />
                <polyline fill="none" stroke={tokens.colors.status.warning} strokeWidth={1.6} strokeDasharray="4,3" points={p80Polyline} />
                <polyline fill="none" stroke={tokens.colors.status.critical} strokeWidth={1.5} strokeDasharray="2,2" points={p95Polyline} />

                {/* Hover Cursor Vertical Indicator */}
                {hoverIndex !== null && hoverIndex < p50.length && (
                  <g>
                    <line
                      x1={getX(hoverIndex)}
                      y1={padTop}
                      x2={getX(hoverIndex)}
                      y2={chartHeight - padBottom}
                      stroke={tokens.colors.border.focus}
                      strokeWidth={1}
                      strokeDasharray="2,2"
                    />
                    <circle cx={getX(hoverIndex)} cy={getY(p50[hoverIndex])} r={3} fill={tokens.colors.brand.primary} />
                    <circle cx={getX(hoverIndex)} cy={getY(p80[hoverIndex])} r={3} fill={tokens.colors.status.warning} />
                    <circle cx={getX(hoverIndex)} cy={getY(p95[hoverIndex])} r={3} fill={tokens.colors.status.critical} />
                  </g>
                )}

                {/* Invisible hover trigger columns */}
                {p50.map((_, idx) => (
                  <rect
                    key={idx}
                    x={getX(idx) - (chartWidth - padLeft - padRight) / horizon / 2}
                    y={padTop}
                    width={(chartWidth - padLeft - padRight) / horizon}
                    height={chartHeight - padTop - padBottom}
                    fill="transparent"
                    onMouseEnter={() => setHoverIndex(idx)}
                  />
                ))}

                {/* X-Axis Monospace Intervals */}
                {[0, Math.floor(horizon / 4), Math.floor(horizon / 2), Math.floor((3 * horizon) / 4), horizon - 1].map((hIdx) => (
                  <text
                    key={hIdx}
                    x={getX(hIdx)}
                    y={chartHeight - 8}
                    textAnchor="middle"
                    fill={tokens.colors.text.muted}
                    fontSize="8.5"
                    fontFamily={tokens.typography.fontMono}
                  >
                    +{hIdx}h
                  </text>
                ))}
              </svg>
            )}

            {/* Hover Tooltip */}
            {hoverIndex !== null && hoverIndex < p50.length && (
              <div
                className="custom-tooltip"
                style={{
                  top: '8px',
                  left: `${Math.min(chartWidth - 130, Math.max(padLeft, getX(hoverIndex) + 10))}px`,
                }}
              >
                <div style={{ fontWeight: 700, marginBottom: '2px', color: tokens.colors.text.primary, fontFamily: tokens.typography.fontMono }}>
                  T+{hoverIndex}h
                </div>
                <div style={{ color: tokens.colors.brand.primary, fontFamily: tokens.typography.fontMono }}>
                  P50: {p50[hoverIndex].toFixed(1)} u
                </div>
                <div style={{ color: tokens.colors.status.warning, fontFamily: tokens.typography.fontMono }}>
                  P80: {p80[hoverIndex].toFixed(1)} u
                </div>
                <div style={{ color: tokens.colors.status.critical, fontFamily: tokens.typography.fontMono }}>
                  P95: {p95[hoverIndex].toFixed(1)} u
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right: Projected Inventory Trajectory & Stockout Outlook */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 700,
                color: tokens.colors.text.secondary,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              STOCKOUT & SAFETY STOCK OUTLOOK
            </span>
            <span className="badge badge-warning">P80 CONSUMPTION</span>
          </div>

          {/* Metric Trio Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', marginBottom: '8px' }}>
            <div
              style={{
                backgroundColor: tokens.colors.background.secondary,
                padding: '7px 8px',
                borderRadius: tokens.radii.badge,
                border: `1px solid ${tokens.colors.border.subtle}`,
              }}
            >
              <div style={{ fontSize: '9px', color: tokens.colors.text.muted, letterSpacing: '0.04em' }}>
                STOCKOUT PROB
              </div>
              <div
                className="font-mono"
                style={{
                  fontSize: '16px',
                  fontWeight: 800,
                  color: forecastData?.stockout_probability && forecastData.stockout_probability > 0.5 ? tokens.colors.status.critical : tokens.colors.status.healthy,
                  marginTop: '1px',
                }}
              >
                {forecastData?.stockout_probability !== undefined && forecastData?.stockout_probability !== null
                  ? `${(forecastData.stockout_probability * 100).toFixed(0)}%`
                  : 'N/A'}
              </div>
            </div>

            <div
              style={{
                backgroundColor: tokens.colors.background.secondary,
                padding: '7px 8px',
                borderRadius: tokens.radii.badge,
                border: `1px solid ${tokens.colors.border.subtle}`,
              }}
            >
              <div style={{ fontSize: '9px', color: tokens.colors.text.muted, letterSpacing: '0.04em' }}>
                SAFETY BREACH
              </div>
              <div
                className="font-mono"
                style={{
                  fontSize: '16px',
                  fontWeight: 800,
                  color: tokens.colors.status.warning,
                  marginTop: '1px',
                }}
              >
                {forecastData?.time_to_safety_stock_hours !== undefined && forecastData?.time_to_safety_stock_hours !== null
                  ? `+${forecastData.time_to_safety_stock_hours}h`
                  : 'N/A'}
              </div>
            </div>

            <div
              style={{
                backgroundColor: tokens.colors.background.secondary,
                padding: '7px 8px',
                borderRadius: tokens.radii.badge,
                border: `1px solid ${tokens.colors.border.subtle}`,
              }}
            >
              <div style={{ fontSize: '9px', color: tokens.colors.text.muted, letterSpacing: '0.04em' }}>
                TIME TO ZERO
              </div>
              <div
                className="font-mono"
                style={{
                  fontSize: '16px',
                  fontWeight: 800,
                  color: tokens.colors.status.critical,
                  marginTop: '1px',
                }}
              >
                {forecastData?.time_to_zero_hours !== undefined && forecastData?.time_to_zero_hours !== null
                  ? `+${forecastData.time_to_zero_hours}h`
                  : 'N/A'}
              </div>
            </div>
          </div>

          {/* Mini Inventory Curve SVG */}
          <div
            style={{
              flex: 1,
              backgroundColor: tokens.colors.background.app,
              borderRadius: tokens.radii.card,
              border: `1px solid ${tokens.colors.border.subtle}`,
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <svg width="100%" height="100%" viewBox={`0 0 ${chartWidth} ${chartHeight - 40}`}>
              {/* Zero Line */}
              <line
                x1={padLeft}
                y1={getInvY(0)}
                x2={chartWidth - padRight}
                y2={getInvY(0)}
                stroke={tokens.colors.status.critical}
                strokeWidth={1}
                strokeDasharray="3,3"
                opacity={0.8}
              />
              <text x={padLeft - 6} y={getInvY(0) + 3} textAnchor="end" fill={tokens.colors.status.critical} fontSize="8" fontFamily={tokens.typography.fontMono}>
                0
              </text>

              {/* Dynamic Safety Stock Line */}
              {forecastData?.dynamic_safety_stock && (
                <g>
                  <line
                    x1={padLeft}
                    y1={getInvY(forecastData.dynamic_safety_stock)}
                    x2={chartWidth - padRight}
                    y2={getInvY(forecastData.dynamic_safety_stock)}
                    stroke={tokens.colors.status.warning}
                    strokeWidth={1}
                    strokeDasharray="2,2"
                    opacity={0.7}
                  />
                  <text
                    x={chartWidth - padRight + 2}
                    y={getInvY(forecastData.dynamic_safety_stock) + 3}
                    fill={tokens.colors.status.warning}
                    fontSize="8"
                    fontFamily={tokens.typography.fontMono}
                  >
                    SS
                  </text>
                </g>
              )}

              {/* Trajectory */}
              {invPolyline && (
                <polyline fill="none" stroke={tokens.colors.brand.primary} strokeWidth={2} points={invPolyline} />
              )}
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForecastPanel;
