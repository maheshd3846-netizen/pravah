"""Graph-Based Risk Propagation Engine for PRAVAH Logistics Network.

Propagates upstream supplier disruption downstream based on supply dependency strengths
and geometric decay over topological hops, preventing infinite loops and runaway cascading.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any, Optional
import networkx as nx


@dataclass
class PropagationConfig:
    """Configurable parameters governing risk propagation across supply chains."""
    propagation_factor: float = 0.50  # maximum fraction of upstream risk transferred
    propagation_decay: float = 0.70   # decay per hop (hop 1: 0.70, hop 2: 0.49, hop 3: 0.34)
    max_depth: int = 3                # maximum topological hops to traverse


class NetworkRiskPropagator:
    """Calculates directional supply dependencies and propagates cascading risk."""

    def __init__(self, config: Optional[PropagationConfig] = None):
        self.config = config or PropagationConfig()

    def build_dependency_graph(
        self,
        nodes: Dict[str, Any],
        routes: Dict[str, Any],
        historical_flows: Optional[Dict[Tuple[str, str], float]] = None,
    ) -> nx.DiGraph:
        """Constructs a directed supply dependency graph where edge weights reflect dependency fraction."""
        graph = nx.DiGraph()

        for nid in nodes:
            graph.add_node(nid)

        # Calculate dependency weights from upstream sources to downstream destinations
        # If historical flows are not provided, estimate from inverse route distance / capacity
        inflow_capacities: Dict[str, float] = {}
        route_edges: List[Tuple[str, str, float]] = []

        for r in routes.values():
            src = getattr(r, "source_node_id", r.get("source_node_id") if isinstance(r, dict) else None)
            dst = getattr(r, "destination_node_id", r.get("destination_node_id") if isinstance(r, dict) else None)
            cap = getattr(r, "max_capacity", r.get("max_capacity", 10000.0) if isinstance(r, dict) else 10000.0)

            if src and dst:
                if historical_flows and (src, dst) in historical_flows:
                    flow = historical_flows[(src, dst)]
                else:
                    flow = float(cap)
                route_edges.append((src, dst, flow))
                inflow_capacities[dst] = inflow_capacities.get(dst, 0.0) + flow

        for src, dst, flow in route_edges:
            total_inflow = inflow_capacities.get(dst, 1.0)
            dependency = flow / max(1.0, total_inflow)
            graph.add_edge(src, dst, dependency=round(dependency, 3))

        return graph

    def propagate_risk(
        self,
        graph: nx.DiGraph,
        base_risks: Dict[str, float],
    ) -> Dict[str, Dict[str, float]]:
        """Propagates upstream disruption risk downstream along directed supply paths."""
        propagated_risks: Dict[str, float] = {}
        impact_sources: Dict[str, List[Dict[str, Any]]] = {nid: [] for nid in graph.nodes}

        for target_node in graph.nodes:
            local_risk = base_risks.get(target_node, 0.0)
            cascaded_risk = 0.0

            # Find all upstream suppliers up to max_depth
            # Invert graph search: ancestors that feed into target_node
            # BFS backwards from target_node
            visited = {target_node}
            queue = [(target_node, 1.0, 1)]  # (current_node, cumulative_dependency, depth)

            while queue:
                curr, cum_dep, depth = queue.pop(0)
                if depth > self.config.max_depth:
                    continue

                # Predecessors in directed graph = upstream suppliers
                predecessors = list(graph.predecessors(curr))
                for supplier in predecessors:
                    if supplier in visited:
                        continue
                    visited.add(supplier)

                    edge_dep = graph[supplier][curr].get("dependency", 0.5)
                    step_dep = cum_dep * edge_dep
                    decay = self.config.propagation_decay ** (depth - 1)

                    supplier_risk = base_risks.get(supplier, 0.0)
                    transferred = self.config.propagation_factor * supplier_risk * step_dep * decay

                    cascaded_risk += transferred
                    if transferred > 0.05:
                        impact_sources[target_node].append({
                            "source_node": supplier,
                            "depth": depth,
                            "dependency": round(edge_dep, 2),
                            "transferred_risk": round(transferred, 3),
                        })

                    queue.append((supplier, step_dep, depth + 1))

            # Total risk is combination of local risk and propagated upstream shock
            # Clipped smoothly to 1.0
            total_risk = min(1.0, local_risk + (1.0 - local_risk) * cascaded_risk)
            propagated_risks[target_node] = round(total_risk, 3)

        results = {}
        for nid in graph.nodes:
            results[nid] = {
                "base_risk": round(base_risks.get(nid, 0.0), 3),
                "propagated_risk": propagated_risks[nid],
                "delta": round(propagated_risks[nid] - base_risks.get(nid, 0.0), 3),
                "impact_sources": impact_sources.get(nid, []),
            }

        return results
