"""Scenario Management Service for PRAVAH."""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from simulation.world_generator import DisruptionType
from simulation.disruption_engine import Disruption


class ScenarioService:
    """Manages reading and writing scenarios from data/scenarios storage."""

    def __init__(self, scenarios_dir: Optional[str] = None):
        if scenarios_dir:
            self.scenarios_dir = Path(scenarios_dir)
        else:
            # Resolve relative to project root
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            self.scenarios_dir = base_dir / "data" / "scenarios"

        self._in_memory_custom: Dict[str, Dict[str, Any]] = {}

    def list_scenarios(self) -> List[Dict[str, Any]]:
        """Reads all scenario definition files from scenarios directory and memory."""
        scenarios = []
        if self.scenarios_dir.exists():
            for file_path in sorted(self.scenarios_dir.glob("*.json")):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        scenarios.append(data)
                except Exception:
                    continue

        for custom_scen in self._in_memory_custom.values():
            if not any(s["name"] == custom_scen["name"] for s in scenarios):
                scenarios.append(custom_scen)

        return scenarios

    def get_scenario(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific scenario by name."""
        name_clean = name.strip().upper()
        for sc in self.list_scenarios():
            if sc.get("name", "").upper() == name_clean:
                return sc
        return None

    def create_scenario(self, scenario_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Saves a new scenario definition to in-memory custom store and file."""
        name = scenario_dict["name"].upper()
        scenario_dict["name"] = name
        self._in_memory_custom[name] = scenario_dict

        # Persist to disk if directory exists
        try:
            file_name = f"{name.lower().replace(' ', '_')}.json"
            target_file = self.scenarios_dir / file_name
            with open(target_file, "w", encoding="utf-8") as f:
                json.dump(scenario_dict, f, indent=2)
        except Exception:
            pass

        return scenario_dict

    def load_disruptions(self, scenario_name: str) -> List[Disruption]:
        """Translates a scenario's JSON disruption items into executable Disruption objects."""
        scenario_data = self.get_scenario(scenario_name)
        if not scenario_data:
            return []

        disruptions = []
        for d in scenario_data.get("disruptions", []):
            try:
                disr = Disruption(
                    id=d["id"],
                    type=DisruptionType(d["type"]),
                    target=d["target"],
                    severity=float(d["severity"]),
                    start_time=int(d["start_time"]),
                    duration=int(d["duration"]),
                    impact_factor=float(d["impact_factor"]),
                    description=d.get("description", ""),
                )
                disruptions.append(disr)
            except Exception:
                continue

        return disruptions
