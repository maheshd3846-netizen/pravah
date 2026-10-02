"""SQLAlchemy Entity Models for PRAVAH Logistics & Supply Chain System.

PostgreSQL & PostGIS compatible schema design with SQLite fallback.
"""

from __future__ import annotations
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from backend.app.models.database import Base


class NodeModel(Base):
    __tablename__ = "nodes"

    id = Column(String(64), primary_key=True, index=True)
    code = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    type = Column(String(32), nullable=False)
    priority = Column(Integer, default=3)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation = Column(Float, nullable=False)
    storage_capacity = Column(Float, nullable=False)
    safety_stock_days = Column(Integer, default=7)
    active = Column(Boolean, default=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RouteModel(Base):
    __tablename__ = "routes"

    id = Column(String(64), primary_key=True, index=True)
    route_code = Column(String(32), unique=True, index=True, nullable=False)
    source_node_id = Column(String(64), ForeignKey("nodes.id"), nullable=False)
    destination_node_id = Column(String(64), ForeignKey("nodes.id"), nullable=False)
    distance_km = Column(Float, nullable=False)
    base_travel_hours = Column(Float, nullable=False)
    max_capacity = Column(Float, nullable=False)
    terrain_type = Column(String(32), nullable=False)
    reliability_score = Column(Float, default=1.0)
    weather_sensitivity = Column(Float, default=0.5)
    status = Column(String(32), default="AVAILABLE")
    geometry = Column(JSON, nullable=True)  # GeoJSON LineString
    created_at = Column(DateTime, default=datetime.utcnow)


class SupplyItemModel(Base):
    __tablename__ = "supply_items"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(64), unique=True, nullable=False)
    category = Column(String(32), nullable=False)
    unit = Column(String(16), nullable=False)
    weight_kg_per_unit = Column(Float, default=1.0)
    criticality = Column(Integer, default=1)  # 1 to 5


class VehicleModel(Base):
    __tablename__ = "vehicles"

    id = Column(String(64), primary_key=True, index=True)
    vehicle_code = Column(String(32), unique=True, index=True, nullable=False)
    vehicle_type = Column(String(32), nullable=False)
    capacity = Column(Float, nullable=False)
    current_node_id = Column(String(64), ForeignKey("nodes.id"), nullable=False)
    availability = Column(Boolean, default=True)
    fuel_level = Column(Float, default=1.0)
    status = Column(String(32), default="AVAILABLE")
    created_at = Column(DateTime, default=datetime.utcnow)


class VehicleEventModel(Base):
    __tablename__ = "vehicle_events"

    id = Column(String(64), primary_key=True, index=True)
    vehicle_id = Column(String(64), ForeignKey("vehicles.id"), nullable=False)
    event_type = Column(String(32), nullable=False)  # DISPATCH, ARRIVAL, BREAKDOWN, MAINTENANCE
    timestamp_hour = Column(Integer, nullable=False)
    node_id = Column(String(64), nullable=True)
    route_id = Column(String(64), nullable=True)
    details = Column(JSON, nullable=True)


class WeatherStateModel(Base):
    __tablename__ = "weather_states"

    id = Column(String(64), primary_key=True, index=True)
    node_id = Column(String(64), ForeignKey("nodes.id"), nullable=True)
    region = Column(String(64), nullable=False)
    timestamp_hour = Column(Integer, nullable=False, index=True)
    temperature = Column(Float, nullable=False)
    rainfall = Column(Float, nullable=False)
    wind_speed = Column(Float, nullable=False)
    visibility = Column(Float, nullable=False)
    severity = Column(String(32), default="NORMAL")


class DemandHistoryModel(Base):
    __tablename__ = "demand_history"

    id = Column(String(64), primary_key=True, index=True)
    node_id = Column(String(64), ForeignKey("nodes.id"), nullable=False)
    item = Column(String(32), nullable=False)
    timestamp_hour = Column(Integer, nullable=False, index=True)
    requested_demand = Column(Float, nullable=False)
    fulfilled_demand = Column(Float, default=0.0)
    unmet_demand = Column(Float, default=0.0)


class InventorySnapshotModel(Base):
    __tablename__ = "inventory_snapshots"

    id = Column(String(64), primary_key=True, index=True)
    simulation_run_id = Column(String(64), index=True, nullable=False)
    timestamp_hour = Column(Integer, nullable=False, index=True)
    node_id = Column(String(64), ForeignKey("nodes.id"), nullable=False)
    item = Column(String(32), nullable=False)
    starting_inventory = Column(Float, nullable=False)
    receipts = Column(Float, default=0.0)
    transfers_in = Column(Float, default=0.0)
    transfers_out = Column(Float, default=0.0)
    requested_demand = Column(Float, nullable=False)
    fulfilled_demand = Column(Float, nullable=False)
    unmet_demand = Column(Float, default=0.0)
    ending_inventory = Column(Float, nullable=False)
    days_of_supply = Column(Float, default=0.0)


class InventoryTransactionModel(Base):
    __tablename__ = "inventory_transactions"

    id = Column(String(64), primary_key=True, index=True)
    node_id = Column(String(64), ForeignKey("nodes.id"), nullable=False)
    item = Column(String(32), nullable=False)
    timestamp_hour = Column(Integer, nullable=False)
    transaction_type = Column(String(32), nullable=False)  # INFLOW, CONSUMPTION, EXPIRATION, TRANSFER
    quantity = Column(Float, nullable=False)
    reference_id = Column(String(64), nullable=True)


class ForecastModel(Base):
    __tablename__ = "forecasts"

    id = Column(String(64), primary_key=True, index=True)
    node_id = Column(String(64), ForeignKey("nodes.id"), nullable=False)
    item = Column(String(32), nullable=False)
    timestamp_hour = Column(Integer, nullable=False, index=True)
    forecast_value = Column(Float, nullable=False)
    lower_bound_p10 = Column(Float, nullable=False)
    upper_bound_p90 = Column(Float, nullable=False)
    model_version = Column(String(64), default="xgboost_v1")
    created_at = Column(DateTime, default=datetime.utcnow)


class RiskScoreModel(Base):
    __tablename__ = "risk_scores"

    id = Column(String(64), primary_key=True, index=True)
    node_id = Column(String(64), ForeignKey("nodes.id"), nullable=True)
    route_id = Column(String(64), ForeignKey("routes.id"), nullable=True)
    timestamp_hour = Column(Integer, nullable=False)
    stockout_probability = Column(Float, default=0.0)
    isolation_risk = Column(Float, default=0.0)
    aggregate_risk_score = Column(Float, default=0.0)
    risk_level = Column(String(32), default="LOW")


class ScenarioModel(Base):
    __tablename__ = "scenarios"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(64), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    horizon_hours = Column(Integer, default=336)
    disruptions = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DisruptionModel(Base):
    __tablename__ = "disruptions"

    id = Column(String(64), primary_key=True, index=True)
    scenario_id = Column(String(64), ForeignKey("scenarios.id"), nullable=True)
    type = Column(String(32), nullable=False)
    target = Column(String(64), nullable=False)
    severity = Column(Float, nullable=False)
    start_time = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    impact_factor = Column(Float, nullable=False)
    description = Column(Text, nullable=True)


class ScenarioResultModel(Base):
    __tablename__ = "scenario_results"

    run_id = Column(String(64), primary_key=True, index=True)
    scenario_name = Column(String(64), nullable=False)
    seed = Column(Integer, default=42)
    horizon_hours = Column(Integer, nullable=False)
    total_requested = Column(Float, nullable=False)
    total_fulfilled = Column(Float, nullable=False)
    total_unmet = Column(Float, nullable=False)
    fulfillment_rate = Column(Float, nullable=False)
    stockout_events_count = Column(Integer, default=0)
    earliest_stockout_hour = Column(Integer, nullable=True)
    summary_metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class OptimizationRunModel(Base):
    __tablename__ = "optimization_runs"

    id = Column(String(64), primary_key=True, index=True)
    scenario_name = Column(String(64), nullable=False)
    solver_name = Column(String(64), nullable=False)
    projected_unmet_before = Column(Float, nullable=False)
    projected_unmet_after = Column(Float, nullable=False)
    mitigation_percentage = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class OptimizationDecisionModel(Base):
    __tablename__ = "optimization_decisions"

    id = Column(String(64), primary_key=True, index=True)
    optimization_run_id = Column(String(64), ForeignKey("optimization_runs.id"), nullable=False)
    source_node_id = Column(String(64), nullable=False)
    destination_node_id = Column(String(64), nullable=False)
    item = Column(String(32), nullable=False)
    quantity = Column(Float, nullable=False)
    route_id = Column(String(64), nullable=False)
    vehicle_id = Column(String(64), nullable=False)
    dispatch_hour = Column(Integer, nullable=False)
    estimated_arrival_hour = Column(Integer, nullable=False)
    rationale = Column(Text, nullable=True)


class RecommendationModel(Base):
    __tablename__ = "recommendations"

    id = Column(String(64), primary_key=True, index=True)
    category = Column(String(32), nullable=False)  # REPOSITION, DISPATCH, REROUTE, ALERT
    priority = Column(String(16), default="HIGH")
    action_text = Column(Text, nullable=False)
    expected_impact = Column(Text, nullable=True)
    status = Column(String(32), default="PENDING")  # PENDING, ACCEPTED, REJECTED, EXECUTED
    created_at = Column(DateTime, default=datetime.utcnow)
