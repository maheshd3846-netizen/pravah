import { request } from './client';
import type { OptimizationSolveResponse } from '../types';

export interface OptimizationSolveParams {
  scenario_id?: string;
  demand_policy?: string;
  solver_type?: string;
  objective_weights?: Record<string, number>;
  horizon_hours?: number;
}

export async function solveOptimization(params: OptimizationSolveParams = {}): Promise<OptimizationSolveResponse> {
  return request<OptimizationSolveResponse>('/optimization/solve', {
    method: 'POST',
    body: JSON.stringify({
      scenario_id: params.scenario_id ?? 'COMPOUND_DISRUPTION',
      demand_policy: params.demand_policy ?? 'P80',
      solver_type: params.solver_type ? params.solver_type.toUpperCase() : 'MILP',
      objective_weights: params.objective_weights,
      horizon_hours: params.horizon_hours ?? 72,
    }),
  });
}

export async function getOptimizationRun(runId: string): Promise<OptimizationSolveResponse> {
  return request<OptimizationSolveResponse>(`/optimization/${runId}`);
}
