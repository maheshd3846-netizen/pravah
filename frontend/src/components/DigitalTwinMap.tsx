import React, { useState, useMemo } from 'react';
import type { NodeItem, RouteItem, VehicleItem, NodeRiskDetail } from '../types';

interface DigitalTwinMapProps {
  nodes: NodeItem[];
  routes: RouteItem[];
  vehicles?: VehicleItem[];
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
  const [showContours, setShowContours] = useState<boolean>(true);

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

  const mapWidth = 920;
  const mapHeight = 520;
  const padding = 70;

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
        return '#a855f7';
      case 'FORWARD_POST':
        return '#10b981';
      default:
        return '#94a3b8';
    }
  };

  const selectedNode = nodes.find(
    (n) => n.id === selectedNodeId || n.code === selectedNodeId
  );
  const selectedRoute = routes.find(
    (r) => r.id === selectedRouteId || r.route_code === selectedRouteId
  );

  return (
    <div
      className="card-panel"
      style={{
        position: 'relative',
        height: '100%',
        backgroundColor: '#070b13',
        overflow: 'hidden',
        border: '1px solid rgba(255, 255, 255, 0.1)',
      }}
    >
      {/* Tactical Panel Header */}
      <div className="panel-header">
        <div className="panel-title">
          <span style={{ color: '#00e5ff', fontSize: '13px' }}>❖</span>
          <span>LOGISTICS DIGITAL TWIN</span>
          <span
            style={{
              fontSize: '10px',
              color: '#64748b',
              fontWeight: 400,
              fontFamily: 'var(--font-mono)',
              marginLeft: '4px',
            }}
          >
            // NORTHERN THEATRE SYNTHETIC GRID [43S WB]
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            onClick={() => setShowContours(!showContours)}
            className="btn btn-secondary"
            style={{
              padding: '2px 8px',
              fontSize: '10px',
              color: showContours ? '#00e5ff' : '#64748b',
              borderColor: showContours ? 'rgba(0, 229, 255, 0.4)' : undefined,
            }}
          >
            {showContours ? 'TERRAIN: ON' : 'TERRAIN: OFF'}
          </button>
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
            style={{ padding: '2px 8px', fontSize: '10px', width: '24px' }}
            title="Zoom In"
          >
            +
          </button>
          <button
            onClick={() => setZoom((z) => Math.max(0.6, z - 0.25))}
            className="btn btn-secondary"
            style={{ padding: '2px 8px', fontSize: '10px', width: '24px' }}
            title="Zoom Out"
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

      {/* SVG Tactical Map Canvas Area */}
      <div
        style={{
          flex: 1,
          cursor: isDragging ? 'grabbing' : 'grab',
          position: 'relative',
          overflow: 'hidden',
          backgroundColor: '#070b13',
          backgroundImage:
            'radial-gradient(ellipse 90% 70% at 50% 50%, rgba(14, 23, 40, 0.7) 0%, rgba(6, 9, 16, 0.98) 100%)',
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
            {/* Tactical Glow Filters */}
            <filter id="glow-cyan" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
            <filter id="glow-red" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
            <filter id="glow-emerald" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>

            {/* Pattern for Blocked Route Hazard Striping */}
            <pattern
              id="hazard-stripes"
              width="8"
              height="8"
              patternTransform="rotate(45 0 0)"
              patternUnits="userSpaceOnUse"
            >
              <line x1="0" y1="0" x2="0" y2="8" stroke="#ef4444" strokeWidth="4" />
              <line x1="4" y1="0" x2="4" y2="8" stroke="#1f2937" strokeWidth="4" />
            </pattern>

            {/* Subtle Topo Gradient */}
            <linearGradient id="topo-fade" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#1e3a8a" stopOpacity="0.08" />
              <stop offset="50%" stopColor="#0f172a" stopOpacity="0.15" />
              <stop offset="100%" stopColor="#064e3b" stopOpacity="0.08" />
            </linearGradient>
          </defs>

          {/* 1. Tactical MGRS Coordinates & Elevation Grid Background */}
          <g opacity={0.35}>
            {/* Coordinate Graticules */}
            {[100, 200, 300, 400, 500, 600, 700, 800].map((gx) => (
              <line
                key={`gx-${gx}`}
                x1={gx}
                y1={20}
                x2={gx}
                y2={mapHeight - 20}
                stroke="rgba(255, 255, 255, 0.05)"
                strokeDasharray="2 6"
              />
            ))}
            {[80, 160, 240, 320, 400, 480].map((gy) => (
              <line
                key={`gy-${gy}`}
                x1={20}
                y1={gy}
                x2={mapWidth - 20}
                y2={gy}
                stroke="rgba(255, 255, 255, 0.05)"
                strokeDasharray="2 6"
              />
            ))}

            {/* Reticle Crosshairs at major intersections */}
            {[
              [200, 160],
              [400, 160],
              [600, 160],
              [800, 160],
              [200, 320],
              [400, 320],
              [600, 320],
              [800, 320],
            ].map(([cx, cy], i) => (
              <g key={`cross-${i}`} transform={`translate(${cx}, ${cy})`}>
                <line x1="-5" y1="0" x2="5" y2="0" stroke="rgba(0, 229, 255, 0.3)" strokeWidth="0.8" />
                <line x1="0" y1="-5" x2="0" y2="5" stroke="rgba(0, 229, 255, 0.3)" strokeWidth="0.8" />
              </g>
            ))}
          </g>

          {/* 2. Topographical Himalayan Contour Isolines (Natural Elevation Modeling) */}
          {showContours && (
            <g opacity={0.22}>
              {/* Karakoram Ridge Ridge Contour 5,200m */}
              <path
                d="M 60,110 Q 180,85 320,130 T 560,95 T 780,140 T 900,105"
                fill="none"
                stroke="#38bdf8"
                strokeWidth="1"
                strokeDasharray="4 3"
              />
              {/* High Altitude Plateau Contour 4,600m */}
              <path
                d="M 50,170 Q 200,140 380,200 T 640,165 T 880,210"
                fill="none"
                stroke="#60a5fa"
                strokeWidth="0.8"
              />
              {/* Indus Valley Fracture Line 3,400m */}
              <path
                d="M 70,260 Q 240,290 420,240 T 700,285 T 890,260"
                fill="none"
                stroke="#06b6d4"
                strokeWidth="1.2"
                strokeDasharray="8 4"
              />
              {/* Zanskar Escarpment 4,800m */}
              <path
                d="M 60,360 Q 210,330 390,390 T 660,350 T 880,410"
                fill="none"
                stroke="#38bdf8"
                strokeWidth="0.8"
              />
              {/* Southern Foothill Contour 2,800m */}
              <path
                d="M 50,450 Q 250,420 460,465 T 780,430 T 910,470"
                fill="none"
                stroke="#64748b"
                strokeWidth="0.8"
              />

              {/* Geographic Sector Watermarks */}
              <text x="80" y="70" fill="rgba(255, 255, 255, 0.15)" fontSize="9" fontFamily="var(--font-mono)" letterSpacing="0.1em">
                ▲ KARAKORAM SECTOR // ELEVATION 5,400m MSL
              </text>
              <text x="520" y="270" fill="rgba(0, 229, 255, 0.15)" fontSize="9" fontFamily="var(--font-mono)" letterSpacing="0.1em">
                ≈ INDUS RIVER BASIN TRANSIT CORRIDOR
              </text>
              <text x="80" y="475" fill="rgba(255, 255, 255, 0.15)" fontSize="9" fontFamily="var(--font-mono)" letterSpacing="0.1em">
                ▲ ZANSKAR RANGE // HIGH-ALTITUDE COMBAT RIDGE
              </text>
            </g>
          )}

          {/* 3. Corridors & Supply Routes */}
          {routes.map((route) => {
            const src = nodeMap.get(route.source_node_id);
            const dst = nodeMap.get(route.destination_node_id);
            if (!src || !dst) return null;

            const p1 = project(src.latitude, src.longitude);
            const p2 = project(dst.latitude, dst.longitude);

            const isBlocked = route.status === 'BLOCKED';
            const isDegraded = route.status === 'DEGRADED';
            const isSelected =
              selectedRouteId === route.id || selectedRouteId === route.route_code;
            const isHighlighted =
              highlightedRouteId === route.id ||
              highlightedRouteId === route.route_code;

            let strokeColor = '#1e2d4a';
            let strokeDash = 'none';
            let strokeWidth = 2.2;

            if (isBlocked) {
              strokeColor = '#ef4444';
              strokeDash = '6,4';
              strokeWidth = 3;
            } else if (isDegraded) {
              strokeColor = '#f59e0b';
              strokeDash = '5,4';
              strokeWidth = 2.6;
            } else if (isSelected) {
              strokeColor = '#00e5ff';
              strokeWidth = 3.5;
            } else if (isHighlighted) {
              strokeColor = '#10b981';
              strokeWidth = 3.5;
            } else {
              strokeColor = '#2563eb';
              strokeWidth = 2;
            }

            const midX = (p1.x + p2.x) / 2;
            const midY = (p1.y + p2.y) / 2;

            return (
              <g
                key={route.id}
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectRoute(route);
                }}
                style={{ cursor: 'pointer' }}
              >
                {/* Wide invisible hit area for crisp interaction */}
                <line
                  x1={p1.x}
                  y1={p1.y}
                  x2={p2.x}
                  y2={p2.y}
                  stroke="transparent"
                  strokeWidth={16}
                />

                {/* Dark roadbed underlay */}
                <line
                  x1={p1.x}
                  y1={p1.y}
                  x2={p2.x}
                  y2={p2.y}
                  stroke="#050810"
                  strokeWidth={strokeWidth + 3}
                  opacity={0.8}
                />

                {/* Main corridor line */}
                <line
                  x1={p1.x}
                  y1={p1.y}
                  x2={p2.x}
                  y2={p2.y}
                  stroke={strokeColor}
                  strokeWidth={strokeWidth}
                  strokeDasharray={strokeDash}
                  opacity={isSelected || isHighlighted ? 1 : 0.82}
                  filter={
                    isSelected
                      ? 'url(#glow-cyan)'
                      : isHighlighted
                      ? 'url(#glow-emerald)'
                      : isBlocked
                      ? 'url(#glow-red)'
                      : undefined
                  }
                />

                {/* Animated Convoy Pulse for Active/Recommended Route */}
                {(isSelected || isHighlighted || (!isBlocked && route.status === 'AVAILABLE')) && (
                  <circle r={3} fill={isHighlighted ? '#10b981' : isSelected ? '#00e5ff' : '#60a5fa'} opacity={0.9}>
                    <animateMotion
                      path={`M ${p1.x} ${p1.y} L ${p2.x} ${p2.y}`}
                      dur={`${Math.max(3, (route.base_travel_hours || 4) * 0.8)}s`}
                      repeatCount="indefinite"
                    />
                  </circle>
                )}

                {/* Blocked Barrier Marker */}
                {isBlocked && (
                  <g transform={`translate(${midX}, ${midY})`}>
                    <circle r={9} fill="#0b0f19" stroke="#ef4444" strokeWidth={1.8} />
                    <line x1="-4" y1="-4" x2="4" y2="4" stroke="#ef4444" strokeWidth={2} />
                    <line x1="4" y1="-4" x2="-4" y2="4" stroke="#ef4444" strokeWidth={2} />
                  </g>
                )}

                {/* Mountain Pass Elevation Badge on High Altitude Passes */}
                {route.terrain_type === 'HIGH_ALTITUDE_PASS' && !isBlocked && (
                  <g transform={`translate(${midX}, ${midY})`}>
                    <rect
                      x={-14}
                      y={-6}
                      width={28}
                      height={12}
                      rx={2}
                      fill="rgba(10, 16, 28, 0.88)"
                      stroke={isDegraded ? '#f59e0b' : 'rgba(255, 255, 255, 0.15)'}
                      strokeWidth={0.6}
                    />
                    <text
                      textAnchor="middle"
                      dy="2.5"
                      fill={isDegraded ? '#fbbf24' : '#94a3b8'}
                      fontSize="7.5"
                      fontFamily="var(--font-mono)"
                      fontWeight="bold"
                    >
                      ⛰ PASS
                    </text>
                  </g>
                )}
              </g>
            );
          })}

          {/* 4. Nodes (Echelon Depots, Hubs, Transit Points, Forward Posts) */}
          {nodes.map((node) => {
            const pos = project(node.latitude, node.longitude);
            const isSelected =
              selectedNodeId === node.id || selectedNodeId === node.code;
            const nodeColor = getNodeColor(node);
            const isDepot = node.type === 'CENTRAL_DEPOT';
            const isHub = node.type === 'REGIONAL_HUB';
            const isForward = node.type === 'FORWARD_POST';
            const risk = nodeRisks[node.id] || nodeRisks[node.code];
            const isHighRisk =
              risk && (risk.level === 'CRITICAL' || risk.level === 'HIGH');

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
                {/* High Risk Tactical Perimeter Alert */}
                {isHighRisk && (
                  <circle
                    r={20}
                    fill="none"
                    stroke="#ef4444"
                    strokeWidth={1.5}
                    strokeDasharray="4 2"
                    opacity={0.8}
                  >
                    <animate
                      attributeName="r"
                      values="15;26;15"
                      dur="2.4s"
                      repeatCount="indefinite"
                    />
                    <animate
                      attributeName="opacity"
                      values="0.9;0.1;0.9"
                      dur="2.4s"
                      repeatCount="indefinite"
                    />
                  </circle>
                )}

                {/* Selection Reticle Ring */}
                {isSelected && (
                  <g>
                    <circle
                      r={isDepot ? 20 : isHub ? 17 : 14}
                      fill="none"
                      stroke="#00e5ff"
                      strokeWidth={1.8}
                      filter="url(#glow-cyan)"
                      strokeDasharray="6 3"
                    >
                      <animateTransform
                        attributeName="transform"
                        type="rotate"
                        from="0"
                        to="360"
                        dur="10s"
                        repeatCount="indefinite"
                      />
                    </circle>
                  </g>
                )}

                {/* Tactical Echelon Icon Shapes */}
                {isDepot ? (
                  // Central Base Depot: Reinforced Command Diamond
                  <g>
                    <polygon
                      points="0,-14 14,0 0,14 -14,0"
                      fill="#0e1b33"
                      stroke={nodeColor}
                      strokeWidth={2}
                    />
                    <polygon
                      points="0,-8 8,0 0,8 -8,0"
                      fill={nodeColor}
                    />
                  </g>
                ) : isHub ? (
                  // Regional Hub: Hexagon Depot Fortress
                  <g>
                    <polygon
                      points="0,-11 10,-5 10,5 0,11 -10,5 -10,-5"
                      fill="#0e2333"
                      stroke={nodeColor}
                      strokeWidth={1.8}
                    />
                    <circle r={3.5} fill={nodeColor} />
                  </g>
                ) : isForward ? (
                  // Forward Defense Post: Target Crosshair with Fortified Circle
                  <g>
                    <circle
                      r={8.5}
                      fill="#0a2118"
                      stroke={nodeColor}
                      strokeWidth={1.8}
                    />
                    <circle r={3.5} fill={nodeColor} />
                  </g>
                ) : (
                  // Transit Point / Staging Base: Hardened Square Bunker
                  <g>
                    <rect
                      x={-7.5}
                      y={-7.5}
                      width={15}
                      height={15}
                      fill="#1e1833"
                      stroke={nodeColor}
                      strokeWidth={1.8}
                      rx={2}
                    />
                    <rect x={-3} y={-3} width={6} height={6} fill={nodeColor} />
                  </g>
                )}

                {/* Node Code Label */}
                {showLabels && (
                  <g transform="translate(0, 19)">
                    <rect
                      x={-24}
                      y={-8}
                      width={48}
                      height={15}
                      fill="rgba(9, 14, 24, 0.92)"
                      stroke={isSelected ? '#00e5ff' : 'rgba(255, 255, 255, 0.16)'}
                      strokeWidth={0.8}
                      rx={2.5}
                    />
                    <text
                      textAnchor="middle"
                      dy="3"
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

        {/* Tactical Legend Overlay */}
        <div
          style={{
            position: 'absolute',
            bottom: '12px',
            left: '12px',
            backgroundColor: 'rgba(10, 16, 28, 0.9)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '5px',
            padding: '8px 12px',
            fontSize: '10px',
            display: 'flex',
            flexDirection: 'column',
            gap: '4px',
            backdropFilter: 'blur(8px)',
            boxShadow: 'var(--shadow-md)',
            pointerEvents: 'none',
          }}
        >
          <div
            style={{
              fontFamily: 'var(--font-heading)',
              fontWeight: 700,
              color: '#94a3b8',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              fontSize: '10px',
              marginBottom: '2px',
            }}
          >
            GRID ECHELONS
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '8px', height: '8px', transform: 'rotate(45deg)', backgroundColor: '#3b82f6' }} />
            <span style={{ color: '#cbd5e1' }}>Central Depot (CD-01)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '8px', height: '8px', backgroundColor: '#06b6d4', borderRadius: '1px' }} />
            <span style={{ color: '#cbd5e1' }}>Regional Hubs (RH-01..03)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '8px', height: '8px', backgroundColor: '#a855f7' }} />
            <span style={{ color: '#cbd5e1' }}>Transit Bases (SB-01..05)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#10b981' }} />
            <span style={{ color: '#cbd5e1' }}>Forward Posts (FP-01..06)</span>
          </div>
          <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', marginTop: '4px', paddingTop: '4px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '12px', height: '2px', backgroundColor: '#38bdf8' }} />
              <span style={{ color: '#94a3b8' }}>Available</span>
              <span style={{ width: '12px', height: '2px', backgroundColor: '#f59e0b', borderTop: '1px dashed #f59e0b' }} />
              <span style={{ color: '#94a3b8' }}>Degraded</span>
              <span style={{ width: '12px', height: '2px', backgroundColor: '#ef4444', borderTop: '1px dashed #ef4444' }} />
              <span style={{ color: '#94a3b8' }}>Blocked</span>
            </div>
          </div>
        </div>

        {/* Selected Node Floating Tactical HUD Drawer */}
        {selectedNode && (
          <div
            style={{
              position: 'absolute',
              top: '12px',
              right: '12px',
              width: '260px',
              backgroundColor: 'rgba(11, 18, 32, 0.94)',
              border: '1px solid rgba(0, 229, 255, 0.4)',
              borderRadius: '6px',
              padding: '14px',
              boxShadow: 'var(--shadow-lg), 0 0 20px rgba(0, 229, 255, 0.15)',
              backdropFilter: 'blur(12px)',
              zIndex: 30,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div
                  style={{
                    fontSize: '15px',
                    fontWeight: 800,
                    color: '#f8fafc',
                    fontFamily: 'var(--font-mono)',
                    letterSpacing: '0.04em',
                  }}
                >
                  {selectedNode.code}
                </div>
                <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '1px' }}>
                  {selectedNode.name}
                </div>
              </div>
              <span className="badge badge-cyan">{selectedNode.type}</span>
            </div>

            <div
              style={{
                borderTop: '1px solid rgba(255, 255, 255, 0.08)',
                marginTop: '10px',
                paddingTop: '8px',
                fontSize: '11px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                <span className="text-secondary">Elevation MSL:</span>
                <span className="font-mono" style={{ color: '#38bdf8', fontWeight: 600 }}>
                  {selectedNode.elevation}m
                </span>
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
                <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.08)', marginTop: '8px', paddingTop: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className="text-secondary">Overall Risk:</span>
                    <span
                      className={`badge ${
                        nodeRisks[selectedNode.id].level === 'CRITICAL' ||
                        nodeRisks[selectedNode.id].level === 'HIGH'
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
              <div style={{ marginTop: '10px' }}>
                <div
                  style={{
                    fontSize: '10px',
                    color: '#64748b',
                    textTransform: 'uppercase',
                    fontFamily: 'var(--font-heading)',
                    fontWeight: 700,
                    letterSpacing: '0.06em',
                    marginBottom: '4px',
                  }}
                >
                  CRITICAL ON-HAND STOCKS
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '5px', fontSize: '10px' }}>
                  {Object.entries(selectedNode.initial_inventory)
                    .slice(0, 4)
                    .map(([item, qty]) => (
                      <div
                        key={item}
                        style={{
                          backgroundColor: 'rgba(255,255,255,0.04)',
                          border: '1px solid rgba(255, 255, 255, 0.06)',
                          padding: '3px 6px',
                          borderRadius: '3px',
                          display: 'flex',
                          justifyContent: 'space-between',
                        }}
                      >
                        <span style={{ color: '#94a3b8' }}>{item}:</span>
                        <span className="font-mono" style={{ color: '#f8fafc', fontWeight: 600 }}>
                          {qty}
                        </span>
                      </div>
                    ))}
                </div>
              </div>

              {onViewIntelligence && (
                <button
                  onClick={() => onViewIntelligence(selectedNode)}
                  className="btn btn-primary"
                  style={{
                    width: '100%',
                    marginTop: '12px',
                    fontSize: '10px',
                    padding: '6px',
                    borderRadius: '4px',
                  }}
                >
                  VIEW INTELLIGENCE ➔
                </button>
              )}
            </div>
          </div>
        )}

        {/* Selected Route Floating Detail Card */}
        {selectedRoute && !selectedNode && (
          <div
            style={{
              position: 'absolute',
              top: '12px',
              right: '12px',
              width: '260px',
              backgroundColor: 'rgba(11, 18, 32, 0.94)',
              border: '1px solid rgba(0, 229, 255, 0.4)',
              borderRadius: '6px',
              padding: '14px',
              boxShadow: 'var(--shadow-lg), 0 0 20px rgba(0, 229, 255, 0.15)',
              backdropFilter: 'blur(12px)',
              zIndex: 30,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div
                  style={{
                    fontSize: '15px',
                    fontWeight: 800,
                    color: '#f8fafc',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  {selectedRoute.route_code}
                </div>
                <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '1px' }}>
                  {selectedRoute.terrain_type}
                </div>
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

            <div
              style={{
                borderTop: '1px solid rgba(255, 255, 255, 0.08)',
                marginTop: '10px',
                paddingTop: '8px',
                fontSize: '11px',
              }}
            >
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
                <span className="font-mono" style={{ color: '#10b981' }}>
                  {(selectedRoute.reliability_score * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
