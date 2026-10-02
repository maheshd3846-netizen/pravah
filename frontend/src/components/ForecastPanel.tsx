import React, { useState } from 'react';
import type { ForecastItemResponse } from '../types';

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

  // Fallback points if forecastData not loaded yet
  const p50 = forecastData?.p50 || [];
  const p80 = forecastData?.p80 || [];
  const p95 = forecastData?.p95 || [];
  const horizon = p50.length || 24;

  const chartWidth = 560;
  const chartHeight = 180;
  const padLeft = 45;
  const padRight = 20;
  const padTop = 15;
  const padBottom = 25;

  const maxVal = Math.max(10, ...p95, ...p80, ...p50) * 1.15;

  const getX = (idx: number) =>
    padLeft + (idx / Math.max(1, horizon - 1)) * (chartWidth - padLeft - padRight);

  const getY = (val: number) =>
    chartHeight - padBottom - (val / maxVal) * (chartHeight - padTop - padBottom);

  // Build SVG polygon for P50-P95 confidence band
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
          <span style={{ color: '#00e5ff', fontSize: '13px' }}>📈</span>
          <span>PREDICTIVE INTELLIGENCE & INVENTORY OUTLOOK</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="badge badge-cyan">{nodeCode}</span>
          <span className="badge badge-neutral">{itemId}</span>
          <span
            style={{
              fontSize: '10px',
              color: '#64748b',
              fontFamily: 'var(--font-mono)',
            }}
          >
            Model: {forecastData?.model_version || 'XGBoost Quantile'}
          </span>
        </div>
      </div>

      <div className="panel-body" style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '16px' }}>
        {/* Left: Multi-Quantile Demand Forecast Chart */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 700,
                color: '#94a3b8',
                textTransform: 'uppercase',
                fontFamily: 'var(--font-heading)',
                letterSpacing: '0.06em',
              }}
            >
              DEMAND FORECAST & UNCERTAINTY BANDS
            </span>
            <div style={{ display: 'flex', gap: '10px', fontSize: '9px', fontFamily: 'var(--font-mono)' }}>
              <span style={{ color: '#38bdf8' }}>— P50 (Median)</span>
              <span style={{ color: '#f59e0b' }}>-- P80 (Planning)</span>
              <span style={{ color: '#ef4444' }}>·· P95 (Stress)</span>
            </div>
          </div>

          <div
            style={{
              position: 'relative',
              width: '100%',
              height: `${chartHeight}px`,
              backgroundColor: '#070b13',
              borderRadius: '5px',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              overflow: 'hidden',
            }}
          >
            {isLoading ? (
              <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontSize: '11px' }}>
                Computing quantile inference...
              </div>
            ) : p50.length === 0 ? (
              <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontSize: '11px' }}>
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
                  <linearGradient id="forecast-band-grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#ef4444" stopOpacity="0.2" />
                    <stop offset="60%" stopColor="#f59e0b" stopOpacity="0.15" />
                    <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.08" />
                  </linearGradient>
                </defs>

                {/* Horizontal Gridlines */}
                {[0.25, 0.5, 0.75, 1.0].map((ratio) => {
                  const yVal = maxVal * ratio;
                  const y = getY(yVal);
                  return (
                    <g key={ratio}>
                      <line
                        x1={padLeft}
                        y1={y}
                        x2={chartWidth - padRight}
                        y2={y}
                        stroke="rgba(255, 255, 255, 0.06)"
                        strokeDasharray="2,2"
                      />
                      <text
                        x={padLeft - 6}
                        y={y + 3}
                        textAnchor="end"
                        fill="#64748b"
                        fontSize="8"
                        fontFamily="var(--font-mono)"
                      >
                        {yVal.toFixed(0)}
                      </text>
                    </g>
                  );
                })}

                {/* Confidence Band: P50 to P95 */}
                {bandPoints && (
                  <polygon points={bandPoints} fill="url(#forecast-band-grad)" />
                )}

                {/* Lines */}
                <polyline fill="none" stroke="#38bdf8" strokeWidth={2} points={p50Polyline} />
                <polyline fill="none" stroke="#f59e0b" strokeWidth={1.6} strokeDasharray="4,3" points={p80Polyline} />
                <polyline fill="none" stroke="#ef4444" strokeWidth={1.6} strokeDasharray="2,2" points={p95Polyline} />

                {/* Hover Guide */}
                {hoverIndex !== null && hoverIndex < p50.length && (
                  <g>
                    <line
                      x1={getX(hoverIndex)}
                      y1={padTop}
                      x2={getX(hoverIndex)}
                      y2={chartHeight - padBottom}
                      stroke="rgba(255, 255, 255, 0.4)"
                      strokeDasharray="2,2"
                    />
                    <circle cx={getX(hoverIndex)} cy={getY(p50[hoverIndex])} r={3.5} fill="#38bdf8" stroke="#070b13" strokeWidth={1} />
                    <circle cx={getX(hoverIndex)} cy={getY(p80[hoverIndex])} r={3.5} fill="#f59e0b" stroke="#070b13" strokeWidth={1} />
                    <circle cx={getX(hoverIndex)} cy={getY(p95[hoverIndex])} r={3.5} fill="#ef4444" stroke="#070b13" strokeWidth={1} />
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

                {/* X-Axis Labels */}
                {[0, Math.floor(horizon / 4), Math.floor(horizon / 2), Math.floor((3 * horizon) / 4), horizon - 1].map((hIdx) => (
                  <text
                    key={hIdx}
                    x={getX(hIdx)}
                    y={chartHeight - 8}
                    textAnchor="middle"
                    fill="#64748b"
                    fontSize="8.5"
                    fontFamily="var(--font-mono)"
                  >
                    +{hIdx}h
                  </text>
                ))}
              </svg>
            )}

            {/* Hover Tooltip Overlay */}
            {hoverIndex !== null && hoverIndex < p50.length && (
              <div
                className="custom-tooltip"
                style={{
                  top: '10px',
                  left: `${Math.min(chartWidth - 140, Math.max(padLeft, getX(hoverIndex) + 10))}px`,
                }}
              >
                <div style={{ fontWeight: 700, marginBottom: '2px', color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
                  Hour +{hoverIndex}
                </div>
                <div style={{ color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>P50: {p50[hoverIndex].toFixed(1)} u/h</div>
                <div style={{ color: '#f59e0b', fontFamily: 'var(--font-mono)' }}>P80: {p80[hoverIndex].toFixed(1)} u/h</div>
                <div style={{ color: '#ef4444', fontFamily: 'var(--font-mono)' }}>P95: {p95[hoverIndex].toFixed(1)} u/h</div>
              </div>
            )}
          </div>
        </div>

        {/* Right: Projected Inventory Trajectory & Stockout Horizon */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 700,
                color: '#94a3b8',
                textTransform: 'uppercase',
                fontFamily: 'var(--font-heading)',
                letterSpacing: '0.06em',
              }}
            >
              STOCKOUT & SAFETY STOCK OUTLOOK
            </span>
            <span className="badge badge-warning">P80 CONSUMPTION</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', marginBottom: '8px' }}>
            <div
              style={{
                backgroundColor: 'rgba(16, 24, 40, 0.75)',
                padding: '8px 10px',
                borderRadius: '4px',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.04)',
              }}
            >
              <div style={{ fontSize: '9px', color: 'var(--text-muted)', fontFamily: 'var(--font-heading)', letterSpacing: '0.04em' }}>
                STOCKOUT PROB
              </div>
              <div
                className="font-mono"
                style={{
                  fontSize: '17px',
                  fontWeight: 800,
                  color: forecastData?.stockout_probability && forecastData.stockout_probability > 0.5 ? '#ef4444' : '#10b981',
                  marginTop: '2px',
                }}
              >
                {forecastData?.stockout_probability !== undefined && forecastData?.stockout_probability !== null
                  ? `${(forecastData.stockout_probability * 100).toFixed(0)}%`
                  : 'N/A'}
              </div>
            </div>

            <div
              style={{
                backgroundColor: 'rgba(16, 24, 40, 0.75)',
                padding: '8px 10px',
                borderRadius: '4px',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.04)',
              }}
            >
              <div style={{ fontSize: '9px', color: 'var(--text-muted)', fontFamily: 'var(--font-heading)', letterSpacing: '0.04em' }}>
                SAFETY BREACH
              </div>
              <div
                className="font-mono"
                style={{
                  fontSize: '17px',
                  fontWeight: 800,
                  color: '#f59e0b',
                  marginTop: '2px',
                }}
              >
                {forecastData?.time_to_safety_stock_hours !== undefined && forecastData?.time_to_safety_stock_hours !== null
                  ? `+${forecastData.time_to_safety_stock_hours}h`
                  : 'N/A'}
              </div>
            </div>

            <div
              style={{
                backgroundColor: 'rgba(16, 24, 40, 0.75)',
                padding: '8px 10px',
                borderRadius: '4px',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.04)',
              }}
            >
              <div style={{ fontSize: '9px', color: 'var(--text-muted)', fontFamily: 'var(--font-heading)', letterSpacing: '0.04em' }}>
                TIME TO ZERO
              </div>
              <div
                className="font-mono"
                style={{
                  fontSize: '17px',
                  fontWeight: 800,
                  color: '#ef4444',
                  marginTop: '2px',
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
              backgroundColor: '#070b13',
              borderRadius: '5px',
              border: '1px solid rgba(255, 255, 255, 0.08)',
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
                stroke="#ef4444"
                strokeWidth={1}
                strokeDasharray="3,3"
                opacity={0.8}
              />
              <text x={padLeft - 6} y={getInvY(0) + 3} textAnchor="end" fill="#ef4444" fontSize="8" fontFamily="var(--font-mono)">
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
                    stroke="#f59e0b"
                    strokeWidth={1}
                    strokeDasharray="2,2"
                    opacity={0.7}
                  />
                  <text
                    x={chartWidth - padRight + 2}
                    y={getInvY(forecastData.dynamic_safety_stock) + 3}
                    fill="#f59e0b"
                    fontSize="8"
                    fontFamily="var(--font-mono)"
                  >
                    SS
                  </text>
                </g>
              )}

              {/* Trajectory */}
              {invPolyline && (
                <polyline fill="none" stroke="#10b981" strokeWidth={2.2} points={invPolyline} />
              )}
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
};
