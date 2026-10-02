"""Decision Variable Indexing and Variable Registry for Matrix Solvers."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional


@dataclass
class FlowVarIndex:
    source_id: str
    destination_id: str
    route_id: str
    item: str
    var_index: int


@dataclass
class ShortageVarIndex:
    node_id: str
    item: str
    var_index: int


@dataclass
class VehicleVarIndex:
    vehicle_id: str
    route_id: str
    var_index: int


class VariableRegistry:
    """Manages index mapping between symbolic supply chain variables and 1D LP/MILP vectors."""

    def __init__(self):
        self.flow_vars: Dict[Tuple[str, str, str, str], FlowVarIndex] = {}
        self.shortage_vars: Dict[Tuple[str, str], ShortageVarIndex] = {}
        self.vehicle_vars: Dict[Tuple[str, str], VehicleVarIndex] = {}
        self.var_names: List[str] = []
        self.lower_bounds: List[float] = []
        self.upper_bounds: List[float] = []
        self.integrality: List[int] = []  # 0: continuous, 1: integer (for scipy.optimize.milp)

    def add_flow_variable(
        self,
        source_id: str,
        destination_id: str,
        route_id: str,
        item: str,
        upper_bound: float = float("inf"),
        is_integer: bool = False,
    ) -> int:
        idx = len(self.var_names)
        name = f"x_{source_id}_{destination_id}_{route_id}_{item}"
        self.var_names.append(name)
        self.lower_bounds.append(0.0)
        self.upper_bounds.append(max(0.0, upper_bound))
        self.integrality.append(1 if is_integer else 0)

        entry = FlowVarIndex(
            source_id=source_id,
            destination_id=destination_id,
            route_id=route_id,
            item=item,
            var_index=idx,
        )
        self.flow_vars[(source_id, destination_id, route_id, item)] = entry
        return idx

    def add_shortage_variable(
        self,
        node_id: str,
        item: str,
        required_demand: float,
    ) -> int:
        idx = len(self.var_names)
        name = f"u_{node_id}_{item}"
        self.var_names.append(name)
        self.lower_bounds.append(0.0)
        self.upper_bounds.append(max(0.0, required_demand))
        self.integrality.append(0)

        entry = ShortageVarIndex(
            node_id=node_id,
            item=item,
            var_index=idx,
        )
        self.shortage_vars[(node_id, item)] = entry
        return idx

    def add_vehicle_variable(
        self,
        vehicle_id: str,
        route_id: str,
    ) -> int:
        idx = len(self.var_names)
        name = f"v_{vehicle_id}_{route_id}"
        self.var_names.append(name)
        self.lower_bounds.append(0.0)
        self.upper_bounds.append(1.0)
        self.integrality.append(1)  # Binary assignment

        entry = VehicleVarIndex(
            vehicle_id=vehicle_id,
            route_id=route_id,
            var_index=idx,
        )
        self.vehicle_vars[(vehicle_id, route_id)] = entry
        return idx

    @property
    def total_variables(self) -> int:
        return len(self.var_names)
