import React, { useState, useMemo } from 'react';
import type { NodeItem, RouteItem, VehicleItem, NodeRiskDetail } from '../types';

interface DigitalTwinMapProps {
  nodes: NodeItem[];
  routes: RouteItem[];
  vehicles: VehicleItem[];
  nodeRisks: Record<string, NodeRiskDetail>;
  selectedNodeId?: string | null;
  onSelectNode: (node: NodeItem) => void;
  onViewIntelligence?: (node: NodeItem) => void;
  selectedRouteId?: string | null;
  onSelectRoute: (route: RouteItem) => void;
  highlightedRouteId?: string | null;
}

export const DigitalTwinMap: React.FC<DigitalTwinMapProps> = ({
  nodes,
  routes,
  vehicles: _vehicles,
  nodeRisks,
  selectedNodeId,
  onSelectNode,
  onViewIntelligence,
  selectedRouteId,
  onSelectRoute,
  highlightedRouteId,
}) => {
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [showLabels, setShowLabels] = useState<boolean>(true);

  // Compute geographical bounds
  const bounds = useMemo(() => {
    if (nodes.length === 0) {
      return { minLat: 34.0, maxLat: 35.5, minLng: 76.0, maxLng: 79.0 };
    }
    const lats = nodes.map((n) => n.latitude);
    const lngs = nodes.map((n) => n.longitude);
    return {
      minLat: Math.min(...lats) - 0.1,
      maxLat: Math.max(...lats) + 0.1,
      minLng: Math.min(...lngs) - 0.15,
      maxLng: Math.max(...lngs) + 0.15,
    };
  }, [nodes]);

  const mapWidth = 900;
  const mapHeight = 520;
  const padding = 60;

  // Projection: Lat/Lng -> SVG coordinates (X, Y)
  const project = (lat: number, lng: number) => {
    const x =
      padding +
      ((lng - bounds.minLng) / (bounds.maxLng - bounds.minLng || 1)) *
        (mapWidth - 2 * padding);
    const y =
      mapHeight -
      padding -
      ((lat - bounds.minLat) / (bounds.maxLat - bounds.minLat || 1)) *
        (mapHeight - 2 * padding);
    return { x, y };
  };

  const nodeMap = useMemo(() => {
    const map = new Map<string, NodeItem>();
    nodes.forEach((n) => {
      map.set(n.id, n);
      map.set(n.code, n);
    });
    return map;
  }, [nodes]);

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  // Node echelon styling
  const getNodeColor = (node: NodeItem) => {
    const risk = nodeRisks[node.id] || nodeRisks[node.code];
    if (risk && (risk.level === 'CRITICAL' || risk.level === 'HIGH')) {
      return '#ef4444';
    }
    switch (node.type) {
      case 'CENTRAL_DEPOT':
        return '#3b82f6';
      case 'REGIONAL_HUB':
        return '#06b6d4';
      case 'TRANSIT_POINT':
        return '#8b5cf6';
      case 'FORWARD_POST':
        return '#10b981';
      default:
        return '#94a3b8';
    }
  };

  const selectedNode = nodes.find((n) => n.id === selectedNodeId || n.code === selectedNodeId);
  const selectedRoute = routes.find((r) => r.id === selectedRouteId || r.route_code === selectedRouteId);

  return (
    <div
      className="card-panel"
      style={{
        position: 'relative',
        height: '100%',
        backgroundColor: '#0c1322',
        overflow: 'hidden',
        border: '1px solid var(--border-subtle)',
      }}
    >
      {/* Panel Header */}
      <div className="panel-header">
        <div className="panel-title">
          <span style={{ color: '#06b6d4' }}>❖</span> LOGISTICS DIGITAL TWIN — NORTHERN SECTOR SYNTHETIC GRID
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={() => setShowLabels(!showLabels)}
            className="btn btn-secondary"
            style={{ padding: '2px 8px', fontSize: '10px' }}
          >
            {showLabels ? 'HIDE LABELS' : 'SHOW LABELS'}
          </button>
          <button
            onClick={() => setZoom((z) => Math.min(2.5, z + 0.25))}
            className="btn btn-secondary"
            style={{ padding: '2px 8px', fontSize: '10px' }}
          >
            +
          </button>
          <button
            onClick={() => setZoom((z) => Math.max(0.6, z - 0.25))}
            className="btn btn-secondary"
            style={{ padding: '2px 8px', fontSize: '10px' }}
          >
            -
          </button>
          <button
            onClick={() => {
              setZoom(1);
              setPan({ x: 0, y: 0 });
            }}
            className="btn btn-secondary"
            style={{ padding: '2px 8px', fontSize: '10px' }}
          >
            RESET
          </button>
        </div>
      </div>

      {/* SVG Canvas Area */}
      <div
        style={{
          flex: 1,
          cursor: isDragging ? 'grabbing' : 'grab',
          position: 'relative',
          overflow: 'hidden',
          backgroundImage:
            'radial-gradient(circle at 50% 50%, rgba(15, 23, 42, 0.4) 0%, rgba(10, 14, 23, 0.95) 100%), linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px)',
          backgroundSize: '100% 100%, 30px 30px, 30px 30px',
        }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <svg
          width="100%"
          height="100%"
          viewBox={`0 0 ${mapWidth} ${mapHeight}`}
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: 'center center',
            transition: isDragging ? 'none' : 'transform 0.1s ease-out',
          }}
        >
          <defs>
            <filter id="glow-cyan" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
            <filter id="glow-red" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* 1. Routes (Corridors) */}
          {routes.map((route) => {
            const src = nodeMap.get(route.source_node_id);
            const dst = nodeMap.get(route.destination_node_id);
            if (!src || !dst) return null;

            const p1 = project(src.latitude, src.longitude);
            const p2 = project(dst.latitude, dst.longitude);

            const isBlocked = route.status === 'BLOCKED';
            const isDegraded = route.status === 'DEGRADED';
            const isSelected = selectedRouteId === route.id || selectedRouteId === route.route_code;
            const isHighlighted = highlightedRouteId === route.id || highlightedRouteId === route.route_code;

            let strokeColor = '#334155';
            let strokeDash = 'none';
            let strokeWidth = 2;

            if (isBlocked) {
              strokeColor = '#ef4444';
              strokeDash = '6,4';
              strokeWidth = 3;
            } else if (isDegraded) {
              strokeColor = '#f59e0b';
              strokeDash = '4,4';
              strokeWidth = 2.5;
            } else {
              strokeColor = isSelected ? '#38bdf8' : isHighlighted ? '#10b981' : '#1e3a8a';
              strokeWidth = isSelected || isHighlighted ? 3 : 2;
            }

            return (
              <g
                key={route.id}
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectRoute(route);
                }}
                style={{ cursor: 'pointer' }}
              >
                {/* Wider invisible hit-test area */}
                <line
                  x1={p1.x}
                  y1={p1.y}
                  x2={p2.x}
                  y2={p2.y}
                  stroke="transparent"
                  strokeWidth={14}
                />
                <line
                  x1={p1.x}
                  y1={p1.y}
                  x2={p2.x}
                  y2={p2.y}
                  stroke={strokeColor}
                  strokeWidth={strokeWidth}
                  strokeDasharray={strokeDash}
                  opacity={isSelected || isHighlighted ? 1 : 0.85}
                  filter={isSelected ? 'url(#glow-cyan)' : isBlocked ? 'url(#glow-red)' : undefined}
                />

                {/* Route Midpoint Badge */}
                {isBlocked && (
                  <g transform={`translate(${(p1.x + p2.x) / 2}, ${(p1.y + p2.y) / 2})`}>
                    <circle r={8} fill="#ef4444" stroke="#0f172a" strokeWidth={1.5} />
                    <text
                      textAnchor="middle"
                      dy="3.5"
                      fill="#ffffff"
                      fontSize="9"
                      fontWeight="bold"
                    >
                      ✕
                    </text>
                  </g>
                )}
              </g>
            );
          })}

          {/* 2. Nodes */}
          {nodes.map((node) => {
            const pos = project(node.latitude, node.longitude);
            const isSelected = selectedNodeId === node.id || selectedNodeId === node.code;
            const nodeColor = getNodeColor(node);
            const isDepot = node.type === 'CENTRAL_DEPOT';
            const isHub = node.type === 'REGIONAL_HUB';
            const isForward = node.type === 'FORWARD_POST';
            const risk = nodeRisks[node.id] || nodeRisks[node.code];
            const isHighRisk = risk && (risk.level === 'CRITICAL' || risk.level === 'HIGH');

            return (
              <g
                key={node.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectNode(node);
                }}
                style={{ cursor: 'pointer' }}
              >
                {/* Risk Pulse Effect */}
                {isHighRisk && (
                  <circle
                    r={18}
                    fill="none"
                    stroke="#ef4444"
                    strokeWidth={1.5}
                    opacity={0.6}
                    strokeDasharray="4,2"
                  >
                    <animate
                      attributeName="r"
                      values="14;24;14"
                      dur="2.5s"
                      repeatCount="indefinite"
                    />
                    <animate
                      attributeName="opacity"
                      values="0.8;0.1;0.8"
                      dur="2.5s"
                      repeatCount="indefinite"
                    />
                  </circle>
                )}

                {/* Outer Selection Ring */}
                {isSelected && (
                  <circle
                    r={isDepot ? 18 : isHub ? 15 : 12}
                    fill="none"
                    stroke="#38bdf8"
                    strokeWidth={2}
                    filter="url(#glow-cyan)"
                  />
                )}

                {/* Node Shape */}
                {isDepot ? (
                  // Central Depot: Solid Diamond
                  <polygon
                    points="0,-12 12,0 0,12 -12,0"
                    fill={nodeColor}
                    stroke="#ffffff"
                    strokeWidth={1.5}
                  />
                ) : isHub ? (
                  // Regional Hub: Hexagon
                  <polygon
                    points="0,-10 9,-5 9,5 0,10 -9,5 -9,-5"
                    fill={nodeColor}
                    stroke="#ffffff"
                    strokeWidth={1.5}
                  />
                ) : isForward ? (
                  // Forward Post: Tactical Target / Shield
                  <circle
                    r={8}
                    fill={nodeColor}
                    stroke="#ffffff"
                    strokeWidth={1.5}
                  />
                ) : (
                  // Staging Base / Transit Point: Square
                  <rect
                    x={-7}
                    y={-7}
                    width={14}
                    height={14}
                    fill={nodeColor}
                    stroke="#ffffff"
                    strokeWidth={1.5}
                  />
                )}

                {/* Node Label */}
                {showLabels && (
                  <g transform="translate(0, 18)">
                    <rect
                      x={-24}
                      y={-8}
                      width={48}
                      height={14}
                      fill="rgba(10, 14, 23, 0.85)"
                      stroke="rgba(255, 255, 255, 0.15)"
                      strokeWidth={0.5}
                      rx={2}
                    />
                    <text
                      textAnchor="middle"
                      dy="2.5"
                      fill={isHighRisk ? '#fca5a5' : '#f8fafc'}
                      fontSize="9"
                      fontWeight="bold"
                      fontFamily="var(--font-mono)"
                    >
                      {node.code}
                    </text>
                  </g>
                )}
              </g>
            );
          })}
        </svg>

        {/* Legend Overlay */}
        <div
          style={{
            position: 'absolute',
            bottom: '12px',
            left: '12px',
            backgroundColor: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '4px',
            padding: '8px 12px',
            fontSize: '10px',
            display: 'flex',
            flexDirection: 'column',
            gap: '4px',
            backdropFilter: 'blur(4px)',
          }}
        >
          <div style={{ fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '2px' }}>
            GRID ECHELONS
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '8px', height: '8px', transform: 'rotate(45deg)', backgroundColor: '#3b82f6' }} />
            <span>Central Depot (CD-01)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '8px', height: '8px', backgroundColor: '#06b6d4', borderRadius: '2px' }} />
            <span>Regional Hubs (RH-01..03)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '8px', height: '8px', backgroundColor: '#8b5cf6' }} />
            <span>Transit Bases (SB-01..05)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#10b981' }} />
            <span>Forward Posts (FP-01..06)</span>
          </div>
          <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', marginTop: '4px', paddingTop: '4px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '12px', height: '2px', backgroundColor: '#38bdf8' }} />
              <span>Available</span>
              <span style={{ width: '12px', height: '2px', backgroundColor: '#f59e0b', borderTop: '1px dashed #f59e0b' }} />
              <span>Degraded</span>
              <span style={{ width: '12px', height: '2px', backgroundColor: '#ef4444', borderTop: '1px dashed #ef4444' }} />
              <span>Blocked</span>
            </div>
          </div>
        </div>

        {/* Selected Node Drawer / Floating Detail Card */}
        {selectedNode && (
          <div
            style={{
              position: 'absolute',
              top: '12px',
              right: '12px',
              width: '240px',
              backgroundColor: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid #38bdf8',
              borderRadius: '6px',
              padding: '12px',
              boxShadow: 'var(--shadow-lg)',
              backdropFilter: 'blur(8px)',
              zIndex: 30,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 800, color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
                  {selectedNode.code}
                </div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>{selectedNode.name}</div>
              </div>
              <span className="badge badge-cyan">{selectedNode.type}</span>
            </div>

            <div style={{ borderTop: '1px solid var(--border-subtle)', marginTop: '8px', paddingTop: '8px', fontSize: '11px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                <span className="text-secondary">Elevation:</span>
                <span className="font-mono">{selectedNode.elevation}m</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                <span className="text-secondary">Storage Cap:</span>
                <span className="font-mono">{selectedNode.storage_capacity.toLocaleString()} u</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                <span className="text-secondary">Safety Stock:</span>
                <span className="font-mono">{selectedNode.safety_stock_days} days</span>
              </div>

              {/* Live Risk Status if present */}
              {nodeRisks[selectedNode.id] && (
                <div style={{ borderTop: '1px solid var(--border-subtle)', marginTop: '6px', paddingTop: '6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className="text-secondary">Overall Risk:</span>
                    <span
                      className={`badge ${
                        nodeRisks[selectedNode.id].level === 'CRITICAL' || nodeRisks[selectedNode.id].level === 'HIGH'
                          ? 'badge-critical'
                          : 'badge-ready'
                      }`}
                    >
                      {nodeRisks[selectedNode.id].level} ({nodeRisks[selectedNode.id].overall_risk.toFixed(2)})
                    </span>
                  </div>
                </div>
              )}

              {/* On-hand Commodity Inventory */}
              <div style={{ marginTop: '8px' }}>
                <div style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', marginBottom: '2px' }}>
                  INITIAL STOCK
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '10px' }}>
                  {Object.entries(selectedNode.initial_inventory).slice(0, 4).map(([item, qty]) => (
                    <div key={item} style={{ backgroundColor: 'rgba(255,255,255,0.04)', padding: '2px 4px', borderRadius: '2px' }}>
                      <span style={{ color: '#94a3b8' }}>{item}:</span> <span className="font-mono">{qty}</span>
                    </div>
                  ))}
                </div>
              </div>

              {onViewIntelligence && (
                <button
                  onClick={() => onViewIntelligence(selectedNode)}
                  className="btn btn-primary"
                  style={{ width: '100%', marginTop: '10px', fontSize: '10px', padding: '5px' }}
                >
                  VIEW INTELLIGENCE ➔
                </button>
              )}
            </div>
          </div>
        )}

        {/* Selected Route Drawer */}
        {selectedRoute && !selectedNode && (
          <div
            style={{
              position: 'absolute',
              top: '12px',
              right: '12px',
              width: '240px',
              backgroundColor: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid #38bdf8',
              borderRadius: '6px',
              padding: '12px',
              boxShadow: 'var(--shadow-lg)',
              backdropFilter: 'blur(8px)',
              zIndex: 30,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 800, color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
                  {selectedRoute.route_code}
                </div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>{selectedRoute.terrain_type}</div>
              </div>
              <span
                className={`badge ${
                  selectedRoute.status === 'BLOCKED'
                    ? 'badge-critical'
                    : selectedRoute.status === 'DEGRADED'
                    ? 'badge-warning'
                    : 'badge-ready'
                }`}
              >
                {selectedRoute.status}
              </span>
            </div>

            <div style={{ borderTop: '1px solid var(--border-subtle)', marginTop: '8px', paddingTop: '8px', fontSize: '11px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                <span className="text-secondary">Distance:</span>
                <span className="font-mono">{selectedRoute.distance_km} km</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                <span className="text-secondary">Transit Time:</span>
                <span className="font-mono">{selectedRoute.base_travel_hours} hours</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                <span className="text-secondary">Corridor Cap:</span>
                <span className="font-mono">{selectedRoute.max_capacity} units</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                <span className="text-secondary">Reliability:</span>
                <span className="font-mono">{(selectedRoute.reliability_score * 100).toFixed(0)}%</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
