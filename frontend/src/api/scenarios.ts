import { request } from './client';
import type { ScenarioItem } from '../types';

export interface SimulationRunParams {
  scenario_name: string;
  seed?: number;
  start_hour?: number;
  horizon_hours?: number;
  auto_replenish?: boolean;
}

export async function fetchScenarios(): Promise<ScenarioItem[]> {
  return request<ScenarioItem[]>('/scenarios');
}

export async function runSimulation(params: SimulationRunParams): Promise<any> {
  return request<any>('/simulation/run', {
    method: 'POST',
    body: JSON.stringify({
      scenario_name: params.scenario_name,
      seed: params.seed ?? 42,
      start_hour: params.start_hour ?? 0,
      horizon_hours: params.horizon_hours ?? 72,
      auto_replenish: params.auto_replenish ?? true,
    }),
  });
}
