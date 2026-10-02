"""Validation and Operational Constraints for Logistics Optimization."""

from __future__ import annotations
from typing import Dict, List, Tuple
from optimization.model import SupplyDecision


def validate_constraints(
    decisions: List[SupplyDecision],
    source_inventories: Dict[str, Dict[str, float]],
    vehicle_capacities: Dict[str, float],
    route_statuses: Dict[str, str],
) -> Tuple[bool, List[str]]:
    """Validates that proposed decisions satisfy physical supply and routing constraints."""
    violations = []

    # 1. Track cumulative source inventory deductions
    consumed: Dict[Tuple[str, str], float] = {}
    for d in decisions:
        consumed[(d.source_node_id, d.item)] = consumed.get((d.source_node_id, d.item), 0.0) + d.quantity

    for (src, item), qty in consumed.items():
        avail = source_inventories.get(src, {}).get(item, 0.0)
        if qty > avail:
            violations.append(f"Source {src} lacks sufficient {item}: required {qty}, available {avail}")

    # 2. Check vehicle capacity constraints
    for d in decisions:
        max_cap = vehicle_capacities.get(d.vehicle_id, 0.0)
        if d.quantity > max_cap:
            violations.append(f"Vehicle {d.vehicle_id} capacity exceeded: load {d.quantity} > max {max_cap}")

    # 3. Check route accessibility
    for d in decisions:
        status = route_statuses.get(d.route_id, "AVAILABLE")
        if status == "BLOCKED":
            violations.append(f"Proposed route {d.route_id} is BLOCKED; cannot dispatch")

    return (len(violations) == 0, violations)
