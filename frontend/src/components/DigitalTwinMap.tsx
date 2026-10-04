import React, { useState, useMemo, useEffect } from 'react';
import type { NodeItem, RouteItem, VehicleItem, NodeRiskDetail } from '../types';
import { tokens } from '../tokens';

interface DigitalTwinMapProps {
  nodes: NodeItem[];
  routes: RouteItem[];
  vehicles?: VehicleItem[];
  nodeRisks: Record<string, NodeRiskDetail>;
  selectedNodeId?: string | null;
  onSelectNode: (node: NodeItem) => void;
  onViewIntelligence?: (node: NodeItem) => void;
  onViewRisk?: (node?: NodeItem) => void;
  selectedRouteId?: string | null;
  onSelectRoute: (route: RouteItem) => void;
  highlightedRouteId?: string | null;
  children?: React.ReactNode;
}

export const DigitalTwinMap: React.FC<DigitalTwinMapProps> = ({
  nodes,
  routes,
  vehicles = [],
  nodeRisks,
  selectedNodeId,
  onSelectNode,
  onViewIntelligence,
  onViewRisk,
  selectedRouteId,
  onSelectRoute,
  highlightedRouteId,
  children,
}) => {
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [showLabels, setShowLabels] = useState<boolean>(true);
  const [showContours, setShowContours] = useState<boolean>(true);
  const [hoveredNode, setHoveredNode] = useState<NodeItem | null>(null);

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

  // Close inspection drawer on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (selectedNodeId) onSelectNode({} as any);
        if (selectedRouteId) onSelectRoute({} as any);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedNodeId, selectedRouteId, onSelectNode, onSelectRoute]);

  // Node hierarchy radius
  const getNodeRadius = (type: string) => {
    switch (type) {
      case 'CENTRAL_DEPOT':
        return 14;
      case 'REGIONAL_HUB':
        return 11;
      case 'TRANSIT_POINT':
        return 8;
      case 'FORWARD_POST':
        return 9;
      default:
        return 8;
    }
  };

  // Node operational status & color
  const getNodeColor = (node: NodeItem) => {
    const risk = nodeRisks[node.id] || nodeRisks[node.code];
    if (risk) {
      if (risk.level === 'CRITICAL') return tokens.colors.status.critical;
      if (risk.level === 'HIGH') return tokens.colors.status.highRisk;
      if (risk.level === 'MODERATE') return tokens.colors.status.warning;
    }
    switch (node.type) {
      case 'CENTRAL_DEPOT':
        return tokens.colors.brand.primary;
      case 'REGIONAL_HUB':
        return tokens.colors.status.info;
      case 'FORWARD_POST':
        return tokens.colors.status.healthy;
      default:
        return tokens.colors.text.secondary;
    }
  };

  // Route styling
  const getRouteStroke = (route: RouteItem) => {
    if (route.id === selectedRouteId || route.route_code === selectedRouteId) {
      return '#4EE0BF'; // Selected: teal/bright neutral
    }
    if (route.id === highlightedRouteId || route.route_code === highlightedRouteId) {
      return tokens.colors.brand.primary; // Active/highlighted: teal
    }
    switch (route.status) {
      case 'BLOCKED':
        return tokens.colors.status.critical; // Blocked: red
      case 'DEGRADED':
        return tokens.colors.status.warning; // Degraded: amber
      case 'ACTIVE':
        return tokens.colors.brand.primary; // Active: teal
      default:
        return '#2B3B52'; // Normal route: muted gray-blue
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
        backgroundColor: tokens.colors.background.app,
        overflow: 'hidden',
        border: `1px solid ${tokens.colors.border.subtle}`,
      }}
    >
      {/* Tactical Panel Header */}
      <div className="panel-header">
        <div className="panel-title">
          <span style={{ color: tokens.colors.brand.primary, fontSize: '13px' }}>❖</span>
          <span>LOGISTICS DIGITAL TWIN</span>
          <span
            style={{
              fontSize: '10px',
              color: tokens.colors.text.muted,
              fontWeight: 400,
              fontFamily: tokens.typography.fontMono,
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
              color: showContours ? tokens.colors.brand.primary : tokens.colors.text.muted,
              borderColor: showContours ? tokens.colors.brand.primaryBorder : undefined,
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
          backgroundColor: tokens.colors.background.app,
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
            {/* Pattern for Blocked Route Hazard Striping */}
            <pattern
              id="hazard-stripes"
              width="8"
              height="8"
              patternTransform="rotate(45 0 0)"
              patternUnits="userSpaceOnUse"
            >
              <line x1="0" y1="0" x2="0" y2="8" stroke={tokens.colors.status.critical} strokeWidth="4" />
              <line x1="4" y1="0" x2="4" y2="8" stroke={tokens.colors.background.secondary} strokeWidth="4" />
            </pattern>
          </defs>

          {/* Clean Tactical Grid Lines */}
          <g opacity={0.3}>
            {Array.from({ length: 9 }).map((_, i) => (
              <line
                key={`h-${i}`}
                x1={0}
                y1={i * 60 + 20}
                x2={mapWidth}
                y2={i * 60 + 20}
                stroke={tokens.colors.border.subtle}
                strokeWidth={0.8}
                strokeDasharray="2,4"
              />
            ))}
            {Array.from({ length: 15 }).map((_, i) => (
              <line
                key={`v-${i}`}
                x1={i * 65 + 10}
                y1={0}
                x2={i * 65 + 10}
                y2={mapHeight}
                stroke={tokens.colors.border.subtle}
                strokeWidth={0.8}
                strokeDasharray="2,4"
              />
            ))}
          </g>

          {/* Synthetic Mountain Elevation Contours */}
          {showContours && (
            <g opacity={0.25}>
              <path
                d="M 120 400 Q 240 320 380 340 T 640 280 T 820 180"
                fill="none"
                stroke={tokens.colors.border.default}
                strokeWidth={1}
                strokeDasharray="4,6"
              />
              <path
                d="M 160 440 Q 280 360 420 370 T 680 310 T 860 210"
                fill="none"
                stroke={tokens.colors.border.subtle}
                strokeWidth={0.8}
              />
              <path
                d="M 190 280 Q 320 180 480 210 T 720 140"
                fill="none"
                stroke={tokens.colors.border.default}
                strokeWidth={1}
                strokeDasharray="5,5"
              />
            </g>
          )}

          {/* Corridors / Routes */}
          <g>
            {routes.map((route) => {
              const srcNode = nodeMap.get(route.source_node_id);
              const dstNode = nodeMap.get(route.destination_node_id);
              if (!srcNode || !dstNode) return null;

              const p1 = project(srcNode.latitude, srcNode.longitude);
              const p2 = project(dstNode.latitude, dstNode.longitude);
              const isSelected = selectedRouteId === route.id || selectedRouteId === route.route_code;
              const isHighlighted = highlightedRouteId === route.id || highlightedRouteId === route.route_code;
              const isBlocked = route.status === 'BLOCKED';
              const strokeColor = getRouteStroke(route);

              return (
                <g key={route.id} onClick={() => onSelectRoute(route)} style={{ cursor: 'pointer' }}>
                  {/* Outer click hit target */}
                  <line
                    x1={p1.x}
                    y1={p1.y}
                    x2={p2.x}
                    y2={p2.y}
                    stroke="transparent"
                    strokeWidth={14}
                  />

                  {/* Route Corridor Path */}
                  <line
                    x1={p1.x}
                    y1={p1.y}
                    x2={p2.x}
                    y2={p2.y}
                    stroke={strokeColor}
                    strokeWidth={isSelected || isHighlighted ? 3 : isBlocked ? 2 : 1.5}
                    strokeDasharray={isBlocked ? '6,4' : undefined}
                    opacity={isSelected || isHighlighted ? 1 : isBlocked ? 0.9 : 0.65}
                  />

                  {/* Route Label */}
                  {showLabels && (
                    <text
                      x={(p1.x + p2.x) / 2}
                      y={(p1.y + p2.y) / 2 - 4}
                      fill={isBlocked ? tokens.colors.status.critical : tokens.colors.text.muted}
                      fontSize="9"
                      fontFamily={tokens.typography.fontMono}
                      textAnchor="middle"
                      opacity={0.85}
                    >
                      {route.route_code}
                    </text>
                  )}
                </g>
              );
            })}
          </g>

          {/* Active Vehicles / Convoys */}
          <g>
            {vehicles.map((veh) => {
              const node = nodeMap.get(veh.current_node_id);
              if (!node) return null;
              const pos = project(node.latitude, node.longitude);
              return (
                <g key={veh.id} transform={`translate(${pos.x + 8}, ${pos.y - 8})`}>
                  <rect
                    x={-4}
                    y={-4}
                    width={8}
                    height={8}
                    fill={tokens.colors.background.elevated}
                    stroke={tokens.colors.brand.primary}
                    strokeWidth={1}
                    transform="rotate(45)"
                  />
                  <text
                    x={8}
                    y={3}
                    fill={tokens.colors.brand.primary}
                    fontSize="8"
                    fontFamily={tokens.typography.fontMono}
                  >
                    {veh.vehicle_code}
                  </text>
                </g>
              );
            })}
          </g>

          {/* Logistics Grid Nodes */}
          <g>
            {nodes.map((node) => {
              const pos = project(node.latitude, node.longitude);
              const r = getNodeRadius(node.type);
              const nodeColor = getNodeColor(node);
              const isSelected = selectedNodeId === node.id || selectedNodeId === node.code;
              const risk = nodeRisks[node.id] || nodeRisks[node.code];
              const isCritical = risk && (risk.level === 'CRITICAL' || risk.level === 'HIGH');

              return (
                <g
                  key={node.id}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  onClick={() => onSelectNode(node)}
                  onMouseEnter={() => setHoveredNode(node)}
                  onMouseLeave={() => setHoveredNode(null)}
                  style={{ cursor: 'pointer' }}
                >
                  {/* Selection / Critical Halo */}
                  {isSelected && (
                    <circle
                      r={r + 6}
                      fill="none"
                      stroke={tokens.colors.brand.primary}
                      strokeWidth={1.5}
                      strokeDasharray="3,3"
                    />
                  )}
                  {isCritical && !isSelected && (
                    <circle
                      r={r + 5}
                      fill="none"
                      stroke={tokens.colors.status.critical}
                      strokeWidth={1.2}
                      opacity={0.8}
                    />
                  )}

                  {/* Outer boundary ring for Depot / Hubs */}
                  {node.type === 'CENTRAL_DEPOT' && (
                    <polygon
                      points={`0,-${r + 4} ${r + 4},0 0,${r + 4} -${r + 4},0`}
                      fill="none"
                      stroke={tokens.colors.brand.primary}
                      strokeWidth={1.5}
                    />
                  )}

                  {/* Main Node Body */}
                  <circle
                    r={r}
                    fill={tokens.colors.background.surface}
                    stroke={nodeColor}
                    strokeWidth={2}
                  />

                  {/* Inner Node Core */}
                  <circle
                    r={r * 0.45}
                    fill={nodeColor}
                  />

                  {/* Node Code Label */}
                  {showLabels && (
                    <text
                      y={r + 12}
                      fill={isSelected ? tokens.colors.brand.primary : tokens.colors.text.primary}
                      fontSize="10"
                      fontWeight={isSelected ? 700 : 600}
                      fontFamily={tokens.typography.fontMono}
                      textAnchor="middle"
                      letterSpacing="0.04em"
                    >
                      {node.code}
                    </text>
                  )}
                </g>
              );
            })}
          </g>
        </svg>

        {/* Hover Tooltip (Section: Small concise tooltip) */}
        {hoveredNode && !selectedNode && (
          <div
            style={{
              position: 'absolute',
              top: '12px',
              left: '12px',
              backgroundColor: tokens.colors.background.surface,
              border: `1px solid ${tokens.colors.border.hover}`,
              borderRadius: tokens.radii.card,
              padding: '8px 12px',
              pointerEvents: 'none',
              zIndex: 25,
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.4)',
              maxWidth: '240px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
              <span className="font-mono" style={{ fontWeight: 700, color: tokens.colors.brand.primary, fontSize: '12px' }}>
                {hoveredNode.code}
              </span>
              <span style={{ fontSize: '9px', color: tokens.colors.text.muted, textTransform: 'uppercase' }}>
                {hoveredNode.type.replace('_', ' ')}
              </span>
            </div>
            <div style={{ fontSize: '11px', color: tokens.colors.text.primary, marginTop: '2px', fontWeight: 600 }}>
              {hoveredNode.name}
            </div>
            <div style={{ display: 'flex', gap: '8px', fontSize: '10px', color: tokens.colors.text.secondary, marginTop: '4px' }}>
              <span>Elev: {hoveredNode.elevation}m</span>
              <span>•</span>
              <span style={{ color: tokens.colors.brand.primary }}>Click to inspect</span>
            </div>
          </div>
        )}

        {/* Legend Overlay */}
        <div
          style={{
            position: 'absolute',
            bottom: '12px',
            left: '12px',
            backgroundColor: tokens.colors.background.drawer,
            border: `1px solid ${tokens.colors.border.subtle}`,
            borderRadius: tokens.radii.badge,
            padding: '8px 12px',
            fontSize: '10px',
            color: tokens.colors.text.secondary,
            fontFamily: tokens.typography.fontMono,
            boxShadow: '0 2px 8px rgba(0,0,0,0.5)',
            pointerEvents: 'none',
          }}
        >
          <div style={{ fontWeight: 700, color: tokens.colors.text.primary, marginBottom: '4px', textTransform: 'uppercase' }}>
            ECHELON & CORRIDOR MATRIX
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: tokens.colors.brand.primary }} />
            <span>Central Depot (CD-01)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: tokens.colors.status.info }} />
            <span>Regional Hubs (RH-01..03)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: tokens.colors.status.healthy }} />
            <span>Forward Posts (FP-01..06)</span>
          </div>
          <div style={{ borderTop: `1px solid ${tokens.colors.border.subtle}`, paddingTop: '4px', display: 'flex', gap: '10px' }}>
            <span style={{ color: tokens.colors.brand.primary }}>— Available</span>
            <span style={{ color: tokens.colors.status.warning }}>-- Degraded</span>
            <span style={{ color: tokens.colors.status.critical }}>··· Blocked</span>
          </div>
        </div>

        {/* Selected Node Inspection Drawer (Contextual 380px Drawer) */}
        {selectedNode && (
          <aside
            aria-label="Node Inspection Drawer"
            style={{
              position: 'absolute',
              top: 0,
              right: 0,
              bottom: 0,
              width: '380px',
              backgroundColor: tokens.colors.background.surface,
              borderLeft: `1px solid ${tokens.colors.border.subtle}`,
              padding: '24px 22px',
              boxShadow: '-6px 0 28px rgba(0,0,0,0.45)',
              zIndex: 35,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              overflowY: 'auto',
            }}
          >
            <div>
              {/* Header with Close Button */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                <div>
                  <div
                    style={{
                      fontSize: '18px',
                      fontWeight: 700,
                      color: tokens.colors.text.primary,
                      letterSpacing: '-0.01em',
                    }}
                  >
                    {selectedNode.code}
                  </div>
                  <div style={{ fontSize: '12px', color: tokens.colors.text.secondary, marginTop: '2px' }}>
                    {selectedNode.name}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span
                    className={`badge ${
                      nodeRisks[selectedNode.id]?.level === 'CRITICAL'
                        ? 'badge-critical'
                        : nodeRisks[selectedNode.id]?.level === 'HIGH'
                        ? 'badge-high'
                        : nodeRisks[selectedNode.id]?.level === 'MODERATE'
                        ? 'badge-warning'
                        : 'badge-healthy'
                    }`}
                    style={{ fontSize: '10px', padding: '3px 8px', letterSpacing: '0.04em' }}
                  >
                    {nodeRisks[selectedNode.id]?.level ? `${nodeRisks[selectedNode.id].level} RISK` : 'OPERATIONAL'}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectNode({} as any);
                    }}
                    className="btn btn-secondary"
                    style={{ padding: '2px 7px', fontSize: '10px' }}
                    title="Close drawer"
                  >
                    ✕
                  </button>
                </div>
              </div>

              {/* Inventory breakdown without nested boxes */}
              <div style={{ marginTop: '16px', marginBottom: '14px' }}>
                <div
                  style={{
                    fontSize: '11px',
                    fontWeight: 600,
                    color: tokens.colors.text.muted,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    marginBottom: '8px',
                  }}
                >
                  Inventory
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {Object.entries(selectedNode.initial_inventory || {})
                    .slice(0, 3)
                    .map(([item, qty]) => (
                      <div
                        key={item}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          fontSize: '12px',
                        }}
                      >
                        <span style={{ color: tokens.colors.text.secondary }}>
                          {item.charAt(0) + item.slice(1).toLowerCase()}
                        </span>
                        <span className="font-mono" style={{ color: tokens.colors.text.primary, fontWeight: 600 }}>
                          {qty} U
                        </span>
                      </div>
                    ))}
                </div>
              </div>

              <div style={{ height: '1px', backgroundColor: tokens.colors.border.subtle, margin: '14px 0' }} />

              {/* Demand Pressure */}
              <div style={{ marginBottom: '14px' }}>
                <div
                  style={{
                    fontSize: '11px',
                    fontWeight: 600,
                    color: tokens.colors.text.muted,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    marginBottom: '8px',
                  }}
                >
                  Demand Pressure
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                  <div>
                    <span style={{ color: tokens.colors.text.muted, fontSize: '11px' }}>P50 </span>
                    <span className="font-mono" style={{ color: tokens.colors.brand.primary, fontWeight: 600 }}>853</span>
                  </div>
                  <div>
                    <span style={{ color: tokens.colors.text.muted, fontSize: '11px' }}>P80 </span>
                    <span className="font-mono" style={{ color: tokens.colors.status.warning, fontWeight: 600 }}>1,640</span>
                  </div>
                  <div>
                    <span style={{ color: tokens.colors.text.muted, fontSize: '11px' }}>P95 </span>
                    <span className="font-mono" style={{ color: tokens.colors.status.critical, fontWeight: 600 }}>2,705</span>
                  </div>
                </div>
              </div>

              <div style={{ height: '1px', backgroundColor: tokens.colors.border.subtle, margin: '14px 0' }} />

              {/* Safety Threshold & Stockout Probability */}
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '14px' }}>
                <div>
                  <div style={{ fontSize: '11px', color: tokens.colors.text.muted, marginBottom: '3px' }}>
                    Safety Threshold
                  </div>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: tokens.colors.text.primary }}>
                    1 hour
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '11px', color: tokens.colors.text.muted, marginBottom: '3px' }}>
                    Stockout Probability
                  </div>
                  <div
                    className="font-mono"
                    style={{
                      fontSize: '14px',
                      fontWeight: 700,
                      color: nodeRisks[selectedNode.id]?.level === 'CRITICAL' ? tokens.colors.status.critical : tokens.colors.status.warning,
                    }}
                  >
                    {nodeRisks[selectedNode.id]?.level === 'CRITICAL' ? '100%' : '92%'}
                  </div>
                </div>
              </div>

              <div style={{ height: '1px', backgroundColor: tokens.colors.border.subtle, margin: '14px 0' }} />

              {/* Why Section */}
              <div style={{ marginBottom: '16px' }}>
                <div
                  style={{
                    fontSize: '11px',
                    fontWeight: 600,
                    color: tokens.colors.text.muted,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    marginBottom: '6px',
                  }}
                >
                  Why?
                </div>
                <div style={{ fontSize: '12px', color: tokens.colors.text.secondary, lineHeight: 1.6 }}>
                  <div>• Demand surge</div>
                  <div>• Route blockage</div>
                  <div>• No inbound supply</div>
                </div>
              </div>
            </div>

            {/* Direct Action Buttons */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', paddingTop: '10px' }}>
              {onViewIntelligence && (
                <button
                  onClick={() => onViewIntelligence(selectedNode)}
                  className="btn btn-primary"
                  style={{ width: '100%', justifyContent: 'center', fontSize: '12px', padding: '7px 12px' }}
                >
                  View Forecast →
                </button>
              )}
              <button
                onClick={() => (onViewRisk ? onViewRisk(selectedNode) : onSelectNode(selectedNode))}
                className="btn btn-secondary"
                style={{ width: '100%', justifyContent: 'center', fontSize: '12px', padding: '7px 12px' }}
              >
                View Risk →
              </button>
            </div>
          </aside>
        )}

        {/* Selected Route Inspection Drawer */}
        {selectedRoute && !selectedNode && (
          <aside
            aria-label="Route Inspection Drawer"
            style={{
              position: 'absolute',
              top: 0,
              right: 0,
              bottom: 0,
              width: '320px',
              backgroundColor: tokens.colors.background.surface,
              borderLeft: `1px solid ${tokens.colors.border.subtle}`,
              padding: '20px 18px',
              boxShadow: '-6px 0 24px rgba(0,0,0,0.35)',
              zIndex: 30,
              overflowY: 'auto',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <div>
                <div
                  style={{
                    fontSize: '17px',
                    fontWeight: 700,
                    color: tokens.colors.text.primary,
                  }}
                >
                  {selectedRoute.route_code}
                </div>
                <div style={{ fontSize: '12px', color: tokens.colors.text.secondary, marginTop: '2px' }}>
                  {selectedRoute.terrain_type}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span
                  className={`badge ${
                    selectedRoute.status === 'BLOCKED'
                      ? 'badge-critical'
                      : selectedRoute.status === 'DEGRADED'
                      ? 'badge-warning'
                      : 'badge-healthy'
                  }`}
                >
                  {selectedRoute.status}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectRoute({} as any);
                  }}
                  className="btn btn-secondary"
                  style={{ padding: '2px 7px', fontSize: '10px' }}
                  title="Close drawer"
                >
                  ✕
                </button>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: tokens.colors.text.secondary }}>Distance</span>
                <span className="font-mono" style={{ color: tokens.colors.text.primary, fontWeight: 600 }}>
                  {selectedRoute.distance_km} km
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: tokens.colors.text.secondary }}>Transit Time</span>
                <span className="font-mono" style={{ color: tokens.colors.text.primary, fontWeight: 600 }}>
                  {selectedRoute.base_travel_hours} hours
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: tokens.colors.text.secondary }}>Corridor Capacity</span>
                <span className="font-mono" style={{ color: tokens.colors.text.primary, fontWeight: 600 }}>
                  {selectedRoute.max_capacity} units
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: tokens.colors.text.secondary }}>Reliability</span>
                <span className="font-mono" style={{ color: tokens.colors.status.healthy, fontWeight: 600 }}>
                  {(selectedRoute.reliability_score * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </aside>
        )}

        {/* Floating Overlays */}
        {children}
      </div>
    </div>
  );
};

export default DigitalTwinMap;
